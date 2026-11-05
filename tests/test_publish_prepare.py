import json
import wave
from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.app.publish_prep_service import PublishPrepError, prepare_package
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


def _rendered_run(c, tmp_path: Path, qa_result="pass"):
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
        c.execute(
            "INSERT INTO qa_reports(render_run_id,result,report_json,created_at) VALUES (?,?,?,?)",
            (rrid, qa_result, "{}", "2026-11-05T00:00:00+00:00"))
    return rrid


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_publish_prepare_creates_immutable_package_no_approval_refs(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        rrid = _rendered_run(c, tmp_path)
        out = prepare_package(c, render_run_id=rrid, destination="youtube",
                              action="private_upload", privacy="private", title="T")
        assert out["ok"] and out["package_hash"].startswith("sha256:")
        row = c.execute("SELECT package_json, action FROM publish_packages WHERE id=?",
                        (out["package_id"],)).fetchone()
        assert "approval_refs" not in row["package_json"]
        assert row["action"] == "private_upload"
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_publish_prepare_blocks_failed_qa(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        rrid = _rendered_run(c, tmp_path, qa_result="fail")
        with pytest.raises(PublishPrepError, match="QA failed"):
            prepare_package(c, render_run_id=rrid, destination="youtube",
                            action="private_upload", privacy="private", title="T")
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_publish_prepare_keeps_public_release_distinct(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        rrid = _rendered_run(c, tmp_path)
        out = prepare_package(c, render_run_id=rrid, destination="youtube",
                              action="public_release", privacy="public", title="T")
        assert out["action"] == "public_release"
    finally:
        c.close()
