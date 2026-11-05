from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rabidon.captions.builder import validate_segments, write_ass
from rabidon.db.connection import immediate_tx
from rabidon.db.repositories import media
from rabidon.render.commentary import RenderError, render_commentary_preview
from rabidon.render.finalize import render_final_local
from rabidon.tts.segments import Segment
from rabidon.utils.timeutil import utc_now_iso


class ServiceError(ValueError):
    pass


def _load_plan_segments(conn: sqlite3.Connection, scene_plan_id: int, narration_run_id: int):
    sp = conn.execute("SELECT * FROM scene_plans WHERE id=?", (scene_plan_id,)).fetchone()
    nr = conn.execute("SELECT * FROM narration_runs WHERE id=?", (narration_run_id,)).fetchone()
    if not sp or not nr:
        raise ServiceError("scene plan or narration run not found")
    if sp["status"] != "resolved":
        raise ServiceError("scene plan must be resolved (ADR-010)")
    plan = json.loads(sp["plan_json"])
    segments = [Segment(**r) for r in json.loads(nr["segments_json"])]
    issues = [i for i in validate_segments(segments) if i.code != "hindi_glyph_review"]
    if issues:
        raise ServiceError(json.dumps({"blockers": [i.__dict__ for i in issues]},
                                      ensure_ascii=False))
    nar = Path(nr["narration_path"])
    wav = nar if nar.is_file() and nar.suffix.lower() == ".wav" else None
    return sp, nr, plan, segments, wav


def run_local_preview(conn: sqlite3.Connection, *, scene_plan_id: int, narration_run_id: int,
                      out_dir: Path, title: str = "Preview") -> dict:
    sp, _nr, plan, segments, wav = _load_plan_segments(conn, scene_plan_id, narration_run_id)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ass = out_dir / "captions.ass"
    write_ass(segments, ass)
    try:
        res = render_commentary_preview(scene_plan=plan, narration_wav=wav, ass_path=ass,
                                        out_dir=out_dir)
    except RenderError as e:
        raise ServiceError(str(e)[:800]) from e
    with immediate_tx(conn):
        topic_id, _ = media.get_script_text(conn, int(sp["script_revision_id"]))
        vid = media.create_video_record(conn, topic_id=topic_id,
                                        script_revision_id=int(sp["script_revision_id"]),
                                        scene_plan_id=scene_plan_id,
                                        narration_run_id=narration_run_id)
        rr_cur = conn.execute(
            """INSERT INTO render_runs(video_id,kind,status,manifest_path,manifest_hash,artifact_path,artifact_hash,created_at,updated_at)
               VALUES (?, 'preview','ok',?,?,?,?,?,?)""",
            (vid, res["manifest_path"], res["manifest"]["manifest_hash"],
             res["preview_path"], res["manifest"]["artifact_hash"], utc_now_iso(), utc_now_iso()),
        )
        rrid = int(rr_cur.lastrowid)
        pkg_id, pkg_hash = media.build_preview_package(
            conn, video_id=vid, render_run_id=rrid, artifact_path=res["preview_path"],
            manifest_path=res["manifest_path"], title=title)
    return {"ok": True, "video_id": vid, "render_run_id": rrid,
            "package_id": pkg_id, "package_hash": pkg_hash,
            "preview": res["preview_path"], "manifest": res["manifest_path"]}


def run_local_final(conn: sqlite3.Connection, *, scene_plan_id: int, narration_run_id: int,
                    out_dir: Path, asset_ids: list[int], title: str = "Final") -> dict:
    _sp, _nr, plan, segments, wav = _load_plan_segments(conn, scene_plan_id, narration_run_id)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ass = out_dir / "captions.ass"
    write_ass(segments, ass)
    res = render_final_local(scene_plan=plan, narration_wav=wav, ass_path=ass,
                             asset_ids=list(asset_ids), rights_conn=conn, out_dir=out_dir)
    return {"ok": res["ok"], "qa": res["qa"], "artifact": res.get("artifact")}
