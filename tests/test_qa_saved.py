import json
import wave
from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.qa.media import qa_media_file
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


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_ffprobe_qa_can_be_stored(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        a = tmp_path / "a.wav"; _tone(a)
        plan = resolve_with_segments(build_provisional(1, ["x"]),
                                     import_recorded_segments(["x"], [a]), "t").plan
        res = render_commentary_preview(scene_plan=plan, narration_wav=a, ass_path=None,
                                        out_dir=tmp_path / "o")
        qa = qa_media_file(Path(res["preview_path"]))
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="t", angle="a", format="commentary")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="x")
            vid = media.create_video_record(c, topic_id=tid, script_revision_id=srev)
            c.execute(
                "INSERT INTO render_runs(video_id,kind,status,artifact_path,manifest_path,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (vid, "preview", "ok", res["preview_path"], res["manifest_path"],
                 "2026-11-05T00:00:00+00:00", "2026-11-05T00:00:00+00:00"))
            rrid = int(c.execute("SELECT last_insert_rowid()").fetchone()[0])
            c.execute(
                "INSERT INTO qa_reports(render_run_id,result,report_json,created_at) VALUES (?,?,?,?)",
                (rrid, qa.result, json.dumps(qa.to_dict(), ensure_ascii=False),
                 "2026-11-05T00:00:00+00:00"))
        row = c.execute("SELECT result FROM qa_reports WHERE render_run_id=?", (rrid,)).fetchone()
        assert row["result"] in ("pass", "pass_with_warnings", "fail")
    finally:
        c.close()
