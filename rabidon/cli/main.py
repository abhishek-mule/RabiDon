from __future__ import annotations

import json
from pathlib import Path

import typer

from rabidon.config import load_settings
from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.logging import configure_logging
from rabidon.utils.timeutil import utc_now_iso

app = typer.Typer(help="RabiDon CLI (local-first, approval-gated).")


def _conn():
    s = load_settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.output_dir.mkdir(parents=True, exist_ok=True)
    c = connect(s.db_path)
    migrate(c)
    return c


@app.command()
def init() -> None:
    s = load_settings()
    configure_logging(s.log_level)
    c = _conn()
    c.close()
    typer.echo(json.dumps({"ok": True, "db": str(s.db_path)}, ensure_ascii=False))


@app.command("topic-create")
def topic_create(title: str, angle: str, format: str, audience: str | None = None,
                 priority: int = 5) -> None:
    c = _conn()
    with immediate_tx(c):
        tid = editorial.create_topic(c, title=title, angle=angle, format=format,
                                     audience=audience, priority=priority)
    c.close()
    typer.echo(json.dumps({"topic_id": tid}, ensure_ascii=False))


@app.command("source-add")
def source_add(title: str, source_type: str, url: str | None = None,
               reliability: str = "unknown", notes: str | None = None) -> None:
    c = _conn()
    with immediate_tx(c):
        sid = editorial.add_source(c, title=title, source_type=source_type,
                                   accessed_at=utc_now_iso(), url=url,
                                   reliability=reliability, notes=notes)
    c.close()
    typer.echo(json.dumps({"source_id": sid}, ensure_ascii=False))


@app.command("claim-add")
def claim_add(topic_id: int, text: str, evidence_status: str = "unknown",
              source_id: list[int] = typer.Option(None)) -> None:
    c = _conn()
    with immediate_tx(c):
        cid, rid = editorial.add_claim(c, topic_id=topic_id, text=text,
                                       evidence_status=evidence_status,
                                       source_ids=source_id or [])
    c.close()
    typer.echo(json.dumps({"claim_id": cid, "claim_revision_id": rid}, ensure_ascii=False))


@app.command("claim-review")
def claim_review(claim_id: int, claim_revision_id: int, decision: str, reviewer: str,
                 accepted_wording: str | None = None) -> None:
    c = _conn()
    with immediate_tx(c):
        rid = editorial.review_claim(c, claim_id=claim_id, claim_revision_id=claim_revision_id,
                                     decision=decision, reviewer=reviewer,
                                     accepted_wording=accepted_wording)
    c.close()
    typer.echo(json.dumps({"claim_review_id": rid}, ensure_ascii=False))


@app.command("script-import")
def script_import(topic_id: int, text_file: Path, language: str = "hi-IN",
                  claim_id: list[int] = typer.Option(None)) -> None:
    text = text_file.read_text(encoding="utf-8")
    c = _conn()
    with immediate_tx(c):
        sid, rid = editorial.create_script(c, topic_id=topic_id, text=text,
                                           claim_ids=claim_id or [], language=language)
    c.close()
    typer.echo(json.dumps({"script_id": sid, "script_revision_id": rid}, ensure_ascii=False))


@app.command("script-approve")
def script_approve(script_revision_id: int, reviewer: str) -> None:
    c = _conn()
    with immediate_tx(c):
        gate = editorial.approve_script_revision(c, script_revision_id=script_revision_id,
                                                 reviewer=reviewer)
    c.close()
    out = {"ok": gate.ok, "blockers": gate.blockers}
    typer.echo(json.dumps(out, ensure_ascii=False))
    if not gate.ok:
        raise typer.Exit(code=2)


@app.command("scene-plan-provisional")
def scene_plan_provisional(script_revision_id: int) -> None:
    c = _conn()
    with immediate_tx(c):
        spid = media.create_provisional_scene_plan(c, script_revision_id=script_revision_id)
    c.close()
    typer.echo(json.dumps({"scene_plan_id": spid, "status": "provisional"}, ensure_ascii=False))


@app.command("narration-import-recorded")
def narration_import_recorded(script_revision_id: int, text: list[str],
                              audio: list[Path], work_dir: Path) -> None:
    # Operator supplies recorded narration (ADR-009 fallback). No synthesis/publish.
    c = _conn()
    with immediate_tx(c):
        nid, segs = media.create_narration_from_recorded(
            c, script_revision_id=script_revision_id, texts=list(text),
            audio_paths=[Path(p) for p in audio], work_dir=work_dir)
    c.close()
    bad = [s.index for s in segs if s.status != "ok"]
    typer.echo(json.dumps({"narration_run_id": nid, "segments": len(segs),
                           "blocked_segments": bad}, ensure_ascii=False))


@app.command("scene-plan-resolve")
def scene_plan_resolve(provisional_scene_plan_id: int, narration_run_id: int) -> None:
    c = _conn()
    with immediate_tx(c):
        spid = media.resolve_scene_plan(c, provisional_scene_plan_id=provisional_scene_plan_id,
                                        narration_run_id=narration_run_id)
    c.close()
    typer.echo(json.dumps({"scene_plan_id": spid, "status": "resolved"}, ensure_ascii=False))


@app.command("captions-build")
def captions_build(narration_run_id: int, out_dir: Path) -> None:
    c = _conn()
    srt, ass, qa = media.build_captions_for_narration(c, narration_run_id=narration_run_id,
                                                      out_dir=out_dir)
    qa_path = out_dir / "caption_qa.json"
    qa.save(qa_path)
    c.close()
    typer.echo(json.dumps({"srt": str(srt), "ass": str(ass), "qa": str(qa_path),
                           "result": qa.result}, ensure_ascii=False))


@app.command("video-preview")
def video_preview(scene_plan_id: int, narration_run_id: int, out_dir: Path,
                  title: str = "Preview") -> None:
    """Local preview only. No Telegram/YouTube/public actions."""
    from rabidon.app.media_service import ServiceError, run_local_preview
    c = _conn()
    try:
        out = run_local_preview(c, scene_plan_id=scene_plan_id, narration_run_id=narration_run_id,
                                out_dir=out_dir, title=title)
    except ServiceError as e:
        msg = str(e)
        try:
            typer.echo(msg)
        except Exception:
            typer.echo(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        c.close()
        raise typer.Exit(code=2)
    c.close()
    typer.echo(json.dumps(out, ensure_ascii=False))

@app.command("worker-run-once")
def worker_run_once() -> None:
    """Run one queued local job (no external send/upload handlers)."""
    from rabidon.jobs.handlers import default_handlers
    from rabidon.jobs.worker import run_once
    c = _conn()
    res = run_once(c, worker_id="cli-worker", handlers=default_handlers())
    c.close()
    typer.echo(json.dumps(None if not res else {"job_id": res.job_id, "status": res.status,
                                                "error": res.error}, ensure_ascii=False))


@app.command("job-enqueue")
def job_enqueue(job_type: str, payload_json: str = "{}") -> None:
    from rabidon.jobs.queue import enqueue
    c = _conn()
    jid = enqueue(c, job_type=job_type, payload=json.loads(payload_json))
    c.close()
    typer.echo(json.dumps({"job_id": jid}, ensure_ascii=False))


@app.command("approval-request-create")
def approval_request_create(action: str, object_type: str, object_id: str,
                            object_version: str, object_hash: str,
                            ttl_seconds: int = 3600) -> None:
    """Create exact-action approval request (local record). Token returned once; share only via trusted channel."""
    from rabidon.approvals.service import create_request
    c = _conn()
    with immediate_tx(c):
        req = create_request(c, action=action, object_type=object_type, object_id=object_id,
                             object_version=object_version, object_hash=object_hash,
                             ttl_seconds=ttl_seconds)
    c.close()
    typer.echo(json.dumps({"request_id": req.request_id, "token": req.token,
                           "warning": "token shown once; do not log/persist in plaintext"}, ensure_ascii=False))


@app.command("asset-register")
def asset_register(asset_type: str, local_path: Path, owner: str = "", provenance: str = "") -> None:
    from rabidon.utils.hashing import sha256_file
    h = sha256_file(Path(local_path))
    c = _conn()
    with immediate_tx(c):
        from rabidon.assets.rights import register_asset
        aid = register_asset(c, asset_type=asset_type, local_path=str(local_path),
                             content_hash=h, owner=owner or None, provenance=provenance or None)
    c.close()
    typer.echo(json.dumps({"asset_id": aid, "content_hash": h}, ensure_ascii=False))


@app.command("asset-permit")
def asset_permit(asset_id: int, rights_basis: str, rights_status: str, use: list[str],
                 reviewer: str = "") -> None:
    c = _conn()
    with immediate_tx(c):
        from rabidon.assets.rights import add_permission
        pid = add_permission(c, asset_id=asset_id, rights_basis=rights_basis,
                             rights_status=rights_status, permitted_uses=list(use),
                             reviewer=reviewer or None)
    c.close()
    typer.echo(json.dumps({"asset_permission_id": pid}, ensure_ascii=False))


@app.command("video-render-final-local")
def video_render_final_local(scene_plan_id: int, narration_run_id: int, out_dir: Path,
                             title: str = "Final", asset_id: list[int] = typer.Option(None)) -> None:
    """Local final render only. Checks final_render rights + QA. No upload/send."""
    from rabidon.app.media_service import ServiceError, run_local_final
    c = _conn()
    try:
        res = run_local_final(c, scene_plan_id=scene_plan_id, narration_run_id=narration_run_id,
                              out_dir=out_dir, asset_ids=list(asset_id or []), title=title)
    except ServiceError as e:
        c.close()
        typer.echo(str(e))
        raise typer.Exit(code=2)
    typer.echo(json.dumps(res, ensure_ascii=False))
    c.close()
    if not res["ok"]:
        raise typer.Exit(code=2)


@app.command("lead-create")
def lead_create(source: str, handle: str = "", platform: str = "",
                contact_provenance: str = "") -> None:
    from rabidon.db.repositories import business
    c = _conn()
    with immediate_tx(c):
        lid = business.create_lead(c, source=source, handle=handle or None,
                                   platform=platform or None,
                                   contact_provenance=contact_provenance or None)
    c.close()
    typer.echo(json.dumps({"lead_id": lid}, ensure_ascii=False))


@app.command("outreach-draft-create")
def outreach_draft_create(lead_id: int, observation: str, message_file: Path) -> None:
    """Manual draft only. Sending requires separate approval + opt-out check; no auto-send."""
    from rabidon.db.repositories import business
    msg = Path(message_file).read_text(encoding="utf-8")
    c = _conn()
    with immediate_tx(c):
        did = business.create_outreach_draft(c, lead_id=lead_id, observation=observation,
                                             message_text=msg)
    c.close()
    typer.echo(json.dumps({"draft_id": did, "status": "draft"}, ensure_ascii=False))


@app.command("outreach-can-send")
def outreach_can_send(lead_id: int, draft_id: int, approved_hash: str) -> None:
    from rabidon.db.repositories import business
    c = _conn()
    ok, reason = business.can_send_outreach(c, lead_id=lead_id, draft_id=draft_id,
                                            approved_hash=approved_hash)
    c.close()
    typer.echo(json.dumps({"ok": ok, "reason": reason}, ensure_ascii=False))
    if not ok:
        raise typer.Exit(code=2)


@app.command("publish-prepare")
def publish_prepare(render_run_id: int, destination: str, action: str, title: str,
                    privacy: str = "private", description: str = "",
                    asset_id: list[int] = typer.Option(None)) -> None:
    """Local immutable package + prechecks only. NO upload/send/approval execution."""
    from rabidon.app.publish_prep_service import PublishPrepError, prepare_package
    c = _conn()
    try:
        out = prepare_package(c, render_run_id=render_run_id, destination=destination,
                              action=action, privacy=privacy, title=title,
                              description=description, asset_ids=list(asset_id or []))
    except PublishPrepError as e:
        c.close()
        typer.echo(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        raise typer.Exit(code=2)
    c.close()
    typer.echo(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    app()
