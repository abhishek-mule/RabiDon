from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rabidon.captions.builder import validate_segments, write_ass, write_srt
from rabidon.publish.package import build_package, store_package
from rabidon.qa.report import Check, QaReport
from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
from rabidon.tts.recorded import import_recorded_segments
from rabidon.tts.segments import Segment, segments_to_json
from rabidon.utils.hashing import sha256_file, sha256_json
from rabidon.utils.timeutil import utc_now_iso


def _now() -> str:
    return utc_now_iso()


def get_script_text(conn: sqlite3.Connection, script_revision_id: int) -> tuple[int, str]:
    row = conn.execute(
        """SELECT s.topic_id, r.text FROM script_revisions r
           JOIN scripts s ON s.id=r.script_id WHERE r.id=?""",
        (script_revision_id,),
    ).fetchone()
    if not row:
        raise ValueError("script revision not found")
    return int(row["topic_id"]), str(row["text"])


def create_provisional_scene_plan(conn: sqlite3.Connection, *, script_revision_id: int) -> int:
    _topic_id, text = get_script_text(conn, script_revision_id)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    plan = build_provisional(script_revision_id, lines or [text.strip()])
    row = conn.execute(
        "SELECT COALESCE(MAX(revision),0) AS n FROM scene_plans WHERE script_revision_id=?",
        (script_revision_id,),
    ).fetchone()
    rev = int(row["n"]) + 1
    cur = conn.execute(
        """INSERT INTO scene_plans(script_revision_id,revision,status,plan_json,plan_hash,created_at)
           VALUES (?,?,?, ?,?,?)""",
        (script_revision_id, rev, plan.status,
         json.dumps(plan.plan, ensure_ascii=False, sort_keys=True), plan.plan_hash, _now()),
    )
    return int(cur.lastrowid)


def create_narration_from_recorded(conn: sqlite3.Connection, *, script_revision_id: int,
                                   texts: list[str], audio_paths: list[Path],
                                   work_dir: Path) -> tuple[int, list[Segment]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    segments = import_recorded_segments(texts, [Path(p) for p in audio_paths])
    issues = validate_segments(segments)
    # Store even if issues exist; QA/pipeline will block.
    total_ms = segments[-1].end_ms if segments else 0
    seg_hash = sha256_json([s.__dict__ for s in segments])
    cur = conn.execute(
        """INSERT INTO narration_runs(script_revision_id,provider,voice_id,narration_path,segments_json,total_duration_ms,segments_hash,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (script_revision_id, "recorded", None, str(work_dir), segments_to_json(segments),
         total_ms, seg_hash, _now()),
    )
    return int(cur.lastrowid), segments


def resolve_scene_plan(conn: sqlite3.Connection, *, provisional_scene_plan_id: int,
                       narration_run_id: int) -> int:
    sp = conn.execute("SELECT * FROM scene_plans WHERE id=?", (provisional_scene_plan_id,)).fetchone()
    nr = conn.execute("SELECT * FROM narration_runs WHERE id=?", (narration_run_id,)).fetchone()
    if not sp or not nr:
        raise ValueError("scene plan or narration run not found")
    if sp["status"] != "provisional":
        raise ValueError("scene plan must be provisional")
    from rabidon.scene_planner.planner import ScenePlan
    prov = ScenePlan("provisional", json.loads(sp["plan_json"]))
    raw = json.loads(nr["segments_json"])
    segments = [Segment(**r) for r in raw]
    timing_id = f"nar_{nr['id']}_{nr['segments_hash'][:12]}"
    resolved = resolve_with_segments(prov, segments, timing_revision_id=timing_id)
    row = conn.execute(
        "SELECT COALESCE(MAX(revision),0) AS n FROM scene_plans WHERE script_revision_id=?",
        (sp["script_revision_id"],),
    ).fetchone()
    rev = int(row["n"]) + 1
    cur = conn.execute(
        """INSERT INTO scene_plans(script_revision_id,revision,status,timing_revision_id,plan_json,plan_hash,created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (sp["script_revision_id"], rev, "resolved", timing_id,
         json.dumps(resolved.plan, ensure_ascii=False, sort_keys=True), resolved.plan_hash, _now()),
    )
    return int(cur.lastrowid)


def build_captions_for_narration(conn: sqlite3.Connection, *, narration_run_id: int,
                                 out_dir: Path) -> tuple[Path, Path, QaReport]:
    nr = conn.execute("SELECT segments_json FROM narration_runs WHERE id=?",
                      (narration_run_id,)).fetchone()
    if not nr:
        raise ValueError("narration run not found")
    segments = [Segment(**r) for r in json.loads(nr["segments_json"])]
    issues = validate_segments(segments)
    out_dir.mkdir(parents=True, exist_ok=True)
    srt = out_dir / "captions.srt"
    ass = out_dir / "captions.ass"
    write_srt(segments, srt)
    write_ass(segments, ass)
    qa = QaReport()
    if issues:
        for i in issues:
            qa.add(Check(f"caption_{i.code}", "fail", i.detail))
    else:
        qa.add(Check("captions", "pass", f"{len(segments)} cues"))
    qa.add(Check("hindi_glyph_review", "manual_required", "Human must verify Devanagari glyph rendering"))
    return srt, ass, qa


def create_video_record(conn: sqlite3.Connection, *, topic_id: int, script_revision_id: int,
                        scene_plan_id: int | None = None,
                        narration_run_id: int | None = None) -> int:
    now = _now()
    cur = conn.execute(
        """INSERT INTO videos(topic_id,script_revision_id,scene_plan_id,narration_run_id,template_id,status,created_at,updated_at)
           VALUES (?,?,?,?,?,'created',?,?)""",
        (topic_id, script_revision_id, scene_plan_id, narration_run_id, "commentary_v1", now, now),
    )
    return int(cur.lastrowid)


def build_preview_package(conn: sqlite3.Connection, *, video_id: int, render_run_id: int,
                          artifact_path: str, manifest_path: str, title: str,
                          qa_report_id: int | None = None) -> tuple[int, str]:
    art_hash = sha256_file(Path(artifact_path))
    man_hash = sha256_file(Path(manifest_path))
    pkg, h = build_package(video_id=video_id, render_run_id=render_run_id,
                           artifact_hash=art_hash, manifest_hash=man_hash,
                           destination="local_archive", action="local_preview",
                           privacy="private", title=title, qa_report_id=qa_report_id)
    pkg_id = store_package(conn, video_id=video_id, render_run_id=render_run_id,
                           destination="local_archive", action="local_preview",
                           privacy="private", package=pkg, package_hash=h)
    return pkg_id, h
