import json
import wave
from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.jobs.handlers import handle_render_preview_local
from rabidon.jobs.queue import ClaimedJob, enqueue
from rabidon.render.commentary import ffmpeg_available


def _tone(path: Path, ms=700):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(22050 * ms / 1000)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
        b = bytearray()
        for i in range(n):
            v = 10000 if (i // 40) % 2 == 0 else -10000
            b += int(v).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(b))


def test_render_handler_requests_manual_input_for_silent_narration(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="t", angle="a", format="commentary")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="x")
            spid = media.create_provisional_scene_plan(c, script_revision_id=srev)
        # placeholder/silent path: use recorded import on missing? create silent wav
        sil = tmp_path / "s.wav"
        with wave.open(str(sil), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)
        with immediate_tx(c):
            nid, _ = media.create_narration_from_recorded(c, script_revision_id=srev,
                                                          texts=["x"], audio_paths=[sil],
                                                          work_dir=tmp_path / "n")
            rpid = media.resolve_scene_plan(c, provisional_scene_plan_id=spid, narration_run_id=nid)
        job = ClaimedJob(1, "render_preview_local", {"scene_plan_id": rpid, "narration_run_id": nid,
                                                     "out_dir": str(tmp_path / "o")}, "tok", 1)
        status, err = handle_render_preview_local(c, job)
        assert status == "awaiting_manual_input"
        assert "ADR-009" in (err or "") or "recorded" in (err or "").lower()
    finally:
        c.close()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_render_handler_succeeds_for_ok_recorded_narration(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="t", angle="a", format="commentary")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="x")
            spid = media.create_provisional_scene_plan(c, script_revision_id=srev)
        a = tmp_path / "a.wav"; _tone(a)
        with immediate_tx(c):
            nid, _ = media.create_narration_from_recorded(c, script_revision_id=srev,
                                                          texts=["x"], audio_paths=[a],
                                                          work_dir=tmp_path / "n")
            rpid = media.resolve_scene_plan(c, provisional_scene_plan_id=spid, narration_run_id=nid)
        job = ClaimedJob(1, "render_preview_local", {"scene_plan_id": rpid, "narration_run_id": nid,
                                                     "out_dir": str(tmp_path / "o")}, "tok", 1)
        status, _ = handle_render_preview_local(c, job)
        assert status == "succeeded"
        assert (tmp_path / "o" / "preview.mp4").exists()
    finally:
        c.close()
