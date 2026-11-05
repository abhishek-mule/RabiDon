import json
import logging
import wave
from pathlib import Path

import pytest

from rabidon.app.publish_prep_service import prepare_package
from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.publish.flow import create_publish_approval, execute_mock_attempt
from rabidon.publish.mock_adapters import (
    InMemorySessionRefStore, MockPublisherAdapter, TelegramTransportLiveDisabled,
    YouTubePublisherAdapterLiveDisabled,
)
from rabidon.publish.ports import LiveExternalActionDisabled, ProbeObservation
from rabidon.publish.reconciliation import reconcile
from rabidon.render.commentary import ffmpeg_available, render_commentary_preview
from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
from rabidon.tts.recorded import import_recorded_segments


def _tone(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(22050 * 0.7)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
        b = bytearray()
        for i in range(n):
            v = 10000 if (i // 40) % 2 == 0 else -10000
            b += int(v).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(b))


def _prepared_private(c, tmp_path: Path) -> int:
    a = tmp_path / "a.wav"; _tone(a)
    plan = resolve_with_segments(build_provisional(1, ["x"]),
                                 import_recorded_segments(["x"], [a]), "t").plan
    res = render_commentary_preview(scene_plan=plan, narration_wav=a, ass_path=None,
                                    out_dir=tmp_path / "o")
    with immediate_tx(c):
        tid = editorial.create_topic(c, title="t", angle="a", format="commentary")
        _sid, srev = editorial.create_script(c, topic_id=tid, text="x")
        vid = media.create_video_record(c, topic_id=tid, script_revision_id=srev)
        c.execute(
            "INSERT INTO render_runs(video_id,kind,status,artifact_path,artifact_hash,manifest_path,manifest_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (vid, "preview", "ok", res["preview_path"], res["manifest"]["artifact_hash"],
             res["manifest_path"], res["manifest"]["manifest_hash"],
             "2026-11-05T00:00:00+00:00", "2026-11-05T00:00:00+00:00"))
        rrid = int(c.execute("SELECT last_insert_rowid()").fetchone()[0])
        c.execute("INSERT INTO qa_reports(render_run_id,result,report_json,created_at) VALUES (?,?,?,?)",
                  (rrid, "pass", "{}", "2026-11-05T00:00:00+00:00"))
    out = prepare_package(c, render_run_id=rrid, destination="youtube",
                          action="private_upload", privacy="private", title="T")
    return out["package_id"]


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_mock_e2e_ambiguous_then_reconcile_no_network(tmp_path: Path, caplog):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        pkg_id = _prepared_private(c, tmp_path)
        pkg = c.execute("SELECT package_hash, action, destination FROM publish_packages WHERE id=?",
                        (pkg_id,)).fetchone()
        adapter = MockPublisherAdapter()
        store = InMemorySessionRefStore()
        caplog.set_level(logging.INFO)
        r = execute_mock_attempt(c, publish_package_id=pkg_id, action="private_upload",
                                 destination="youtube", idempotency_key="k1", asset_ids=[],
                                 adapter=adapter, session_store=store,
                                 approved_action="private_upload",
                                 approved_package_hash=pkg["package_hash"],
                                 simulate_ambiguous=True)
        assert r.ok and r.local_state == "reconciliation_required"
        # Opaque ref stored; raw mock secret not equal to ref and not in logs.
        row = c.execute("SELECT upload_session_ref FROM publication_attempts WHERE id=?",
                        (r.attempt_id,)).fetchone()
        assert (row["upload_session_ref"] or "").startswith("sessionref:opaque:")
        assert "mock-session:" not in caplog.text
        adapter.observations[("youtube", "k1", None)] = ProbeObservation(state="uploaded", remote_id="yt1")
        rec = reconcile(c, attempt_id=r.attempt_id, probe=adapter)
        assert rec.local_state == "uploaded" and rec.remote_id == "yt1"
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_private_approval_cannot_authorize_public_release(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        pkg_id = _prepared_private(c, tmp_path)
        pkg = c.execute("SELECT package_hash FROM publish_packages WHERE id=?", (pkg_id,)).fetchone()
        r = execute_mock_attempt(c, publish_package_id=pkg_id, action="private_upload",
                                 destination="youtube", idempotency_key="k2", asset_ids=[],
                                 adapter=MockPublisherAdapter(),
                                 approved_action="public_release",
                                 approved_package_hash=pkg["package_hash"])
        assert r.ok is False
        assert "exact approval" in (r.error or "").lower()
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_package_hash_mismatch_rejected(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        pkg_id = _prepared_private(c, tmp_path)
        r = execute_mock_attempt(c, publish_package_id=pkg_id, action="private_upload",
                                 destination="youtube", idempotency_key="k3", asset_ids=[],
                                 adapter=MockPublisherAdapter(),
                                 approved_action="private_upload",
                                 approved_package_hash="sha256:wrong")
        assert r.ok is False
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_idempotent_attempt_reuses_db_row(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        pkg_id = _prepared_private(c, tmp_path)
        pkg = c.execute("SELECT package_hash FROM publish_packages WHERE id=?", (pkg_id,)).fetchone()
        kw = dict(publish_package_id=pkg_id, action="private_upload", destination="youtube",
                  idempotency_key="k4", asset_ids=[], adapter=MockPublisherAdapter(),
                  approved_action="private_upload", approved_package_hash=pkg["package_hash"],
                  simulate_ambiguous=True)
        a = execute_mock_attempt(c, **kw)
        b = execute_mock_attempt(c, **kw)
        assert a.attempt_id == b.attempt_id
    finally:
        c.close()


def test_live_adapters_disabled():
    with pytest.raises(LiveExternalActionDisabled):
        YouTubePublisherAdapterLiveDisabled().prepare_session(package_hash="x", destination="youtube", action="private_upload")
    with pytest.raises(LiveExternalActionDisabled):
        TelegramTransportLiveDisabled().send_preview(chat_id="1", text="x", artifact_path=None)
