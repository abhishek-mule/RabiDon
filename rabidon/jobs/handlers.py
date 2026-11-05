from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rabidon.db.connection import immediate_tx
from rabidon.db.repositories import media
from rabidon.jobs.queue import ClaimedJob
from rabidon.qa.media import qa_media_file
from rabidon.utils.timeutil import utc_now_iso


def _ok() -> tuple[str, str | None]:
    return "succeeded", None


def _manual(msg: str) -> tuple[str, str | None]:
    return "awaiting_manual_input", msg


def _awaiting(msg: str) -> tuple[str, str | None]:
    return "awaiting_approval", msg


def handle_build_captions(conn: sqlite3.Connection, job: ClaimedJob) -> tuple[str, str | None]:
    nrid = int(job.payload["narration_run_id"])
    out_dir = Path(job.payload["out_dir"])
    srt, ass, qa = media.build_captions_for_narration(conn, narration_run_id=nrid, out_dir=out_dir)
    qa.save(out_dir / "caption_qa.json")
    if qa.result == "fail":
        return "failed", json.dumps(qa.to_dict(), ensure_ascii=False)
    return _ok()


def handle_render_preview_local(conn: sqlite3.Connection, job: ClaimedJob) -> tuple[str, str | None]:
    # Local only. No Telegram/YouTube/send.
    spid = int(job.payload["scene_plan_id"])
    nrid = int(job.payload["narration_run_id"])
    out_dir = Path(job.payload["out_dir"])
    title = job.payload.get("title", "Preview")
    sp = conn.execute("SELECT * FROM scene_plans WHERE id=?", (spid,)).fetchone()
    nr = conn.execute("SELECT * FROM narration_runs WHERE id=?", (nrid,)).fetchone()
    if not sp or not nr:
        return "failed", "scene plan or narration run not found"
    if sp["status"] != "resolved":
        return _manual("scene plan must be resolved (run TTS/timing resolution)")
    from rabidon.captions.builder import validate_segments, write_ass
    from rabidon.render.commentary import RenderError, render_commentary_preview
    from rabidon.tts.segments import Segment
    plan = json.loads(sp["plan_json"])
    segments = [Segment(**r) for r in json.loads(nr["segments_json"])]
    issues = [i for i in validate_segments(segments) if i.code != "hindi_glyph_review"]
    if any(i.code == "segment_status" for i in issues):
        return _manual("narration has failed/silent segments; provide recorded audio (ADR-009)")
    if issues:
        return "failed", json.dumps([i.__dict__ for i in issues], ensure_ascii=False)
    out_dir.mkdir(parents=True, exist_ok=True)
    ass = out_dir / "captions.ass"
    write_ass(segments, ass)
    nar = Path(nr["narration_path"])
    wav = nar if nar.is_file() and nar.suffix.lower() == ".wav" else None
    try:
        res = render_commentary_preview(scene_plan=plan, narration_wav=wav, ass_path=ass, out_dir=out_dir)
    except RenderError as e:
        return "retry_scheduled", str(e)[:800]
    qa = qa_media_file(Path(res["preview_path"]))
    with immediate_tx(conn):
        topic_id, _ = media.get_script_text(conn, int(sp["script_revision_id"]))
        vid = media.create_video_record(conn, topic_id=topic_id,
                                        script_revision_id=int(sp["script_revision_id"]),
                                        scene_plan_id=spid, narration_run_id=nrid)
        rr = conn.execute(
            """INSERT INTO render_runs(video_id,kind,status,manifest_path,manifest_hash,artifact_path,artifact_hash,created_at,updated_at)
               VALUES (?,'preview','ok',?,?,?,?,?,?)""",
            (vid, res["manifest_path"], res["manifest"]["manifest_hash"],
             res["preview_path"], res["manifest"]["artifact_hash"], utc_now_iso(), utc_now_iso()),
        )
        rrid = int(rr.lastrowid)
        conn.execute(
            "INSERT INTO qa_reports(render_run_id,result,report_json,created_at) VALUES (?,?,?,?)",
            (rrid, qa.result, json.dumps(qa.to_dict(), ensure_ascii=False), utc_now_iso()),
        )
        qid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        media.build_preview_package(conn, video_id=vid, render_run_id=rrid,
                                    artifact_path=res["preview_path"],
                                    manifest_path=res["manifest_path"], title=title,
                                    qa_report_id=qid)
    return _ok()


def handle_awaiting_manual(conn: sqlite3.Connection, job: ClaimedJob) -> tuple[str, str | None]:
    return _manual(job.payload.get("reason") or "operator input required (ADR-006/009)")


def handle_publish_requires_approval(conn: sqlite3.Connection, job: ClaimedJob) -> tuple[str, str | None]:
    # Safety: external publish/send is never executed by local handlers.
    return _awaiting("exact operator approval required before any external publish/send; no upload performed")


def default_handlers() -> dict[str, object]:
    return {
        "build_captions": handle_build_captions,
        "render_preview_local": handle_render_preview_local,
        "awaiting_manual_input": handle_awaiting_manual,
        "publish_external_requires_approval": handle_publish_requires_approval,
    }
