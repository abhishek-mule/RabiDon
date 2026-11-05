import json
import wave
from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.render.commentary import ffmpeg_available
from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
from rabidon.tts.recorded import import_recorded_segments


def _tone(path: Path, ms=800):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(22050 * ms / 1000)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
        b = bytearray()
        for i in range(n):
            v = 10000 if (i // 40) % 2 == 0 else -10000
            b += int(v).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(b))


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_local_preview_pipeline_end_to_end(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="T", angle="A", format="commentary")
            src = editorial.add_source(c, title="S", source_type="primary",
                                       accessed_at="2026-11-05T00:00:00+00:00")
            cid, rev = editorial.add_claim(c, topic_id=tid, text="f",
                                           evidence_status="supported", source_ids=[src])
            editorial.review_claim(c, claim_id=cid, claim_revision_id=rev,
                                   decision="accepted", reviewer="t")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="नमस्ते\nदुनिया",
                                                 claim_ids=[cid])
            assert editorial.approve_script_revision(c, script_revision_id=srev, reviewer="t").ok
            spid = media.create_provisional_scene_plan(c, script_revision_id=srev)

        a = tmp_path / "a.wav"; b = tmp_path / "b.wav"
        _tone(a, 600); _tone(b, 700)
        with immediate_tx(c):
            nid, segs = media.create_narration_from_recorded(
                c, script_revision_id=srev, texts=["नमस्ते", "दुनिया"],
                audio_paths=[a, b], work_dir=tmp_path / "nar")
            assert all(s.status == "ok" for s in segs)
            rpid = media.resolve_scene_plan(c, provisional_scene_plan_id=spid, narration_run_id=nid)

        sp = c.execute("SELECT * FROM scene_plans WHERE id=?", (rpid,)).fetchone()
        assert sp["status"] == "resolved"
        plan = json.loads(sp["plan_json"])
        assert plan["scenes"][0]["timeline_start_ms"] == 0

        srt, _ass, qa = media.build_captions_for_narration(c, narration_run_id=nid,
                                                           out_dir=tmp_path / "cap")
        assert srt.exists()
        assert "नमस्ते" in srt.read_text(encoding="utf-8")
        assert qa.result in ("pass", "pass_with_warnings")  # glyph review manual_required

        from rabidon.captions.builder import write_ass
        from rabidon.render.commentary import render_commentary_preview
        from rabidon.tts.segments import Segment
        ass = tmp_path / "cap" / "captions.ass"
        segments = [Segment(**r) for r in json.loads(
            c.execute("SELECT segments_json FROM narration_runs WHERE id=?", (nid,)).fetchone()[0])]
        write_ass(segments, ass)
        res = render_commentary_preview(scene_plan=plan, narration_wav=a, ass_path=ass,
                                        out_dir=tmp_path / "render")
        assert Path(res["preview_path"]).exists()
        pkg = c.execute("SELECT COUNT(*) FROM publish_packages").fetchone()[0] if False else 0
        with immediate_tx(c):
            vid = media.create_video_record(c, topic_id=tid, script_revision_id=srev,
                                            scene_plan_id=rpid, narration_run_id=nid)
            c.execute(
                "INSERT INTO render_runs(video_id,kind,status,manifest_path,manifest_hash,artifact_path,artifact_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (vid, "preview", "ok", res["manifest_path"], res["manifest"]["manifest_hash"],
                 res["preview_path"], res["manifest"]["artifact_hash"],
                 "2026-11-05T00:00:00+00:00", "2026-11-05T00:00:00+00:00"))
            rrid = int(c.execute("SELECT last_insert_rowid()").fetchone()[0])
            _pid, ph = media.build_preview_package(c, video_id=vid, render_run_id=rrid,
                                                   artifact_path=res["preview_path"],
                                                   manifest_path=res["manifest_path"],
                                                   title="Preview")
        assert ph.startswith("sha256:")
        row = c.execute("SELECT package_json FROM publish_packages").fetchone()
        assert "approval_refs" not in row[0]
    finally:
        c.close()
