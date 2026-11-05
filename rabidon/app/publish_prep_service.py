from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rabidon.assets.rights import check_assets_for_use
from rabidon.db.connection import immediate_tx
from rabidon.publish.package import build_package, store_package
from rabidon.utils.hashing import sha256_file

# Map publish action to rights/use gate. Conservative: local package prep requires
# rights evidence for the intended destination action (ADR-002/005).
ACTION_USE = {
    "local_preview": "local_preview",
    "telegram_preview": "external_preview",
    "private_upload": "private_upload",
    "public_release": "public_release",
    "client_delivery": "client_delivery",
}


class PublishPrepError(ValueError):
    pass


def prepare_package(conn: sqlite3.Connection, *, render_run_id: int, destination: str,
                    action: str, privacy: str, title: str, description: str = "",
                    asset_ids: list[int] | None = None) -> dict:
    if action not in ACTION_USE:
        raise PublishPrepError(f"unknown action: {action}")
    rr = conn.execute("SELECT * FROM render_runs WHERE id=?", (render_run_id,)).fetchone()
    if not rr or not rr["artifact_path"] or not rr["manifest_path"]:
        raise PublishPrepError("render run/artifact not found")
    qa = conn.execute(
        "SELECT result FROM qa_reports WHERE render_run_id=? ORDER BY id DESC LIMIT 1",
        (render_run_id,),
    ).fetchone()
    if not qa:
        raise PublishPrepError("QA report required before publish preparation")
    if qa["result"] == "fail":
        raise PublishPrepError("QA failed; package preparation blocked")
    use = ACTION_USE[action]
    rights = check_assets_for_use(conn, asset_ids or [], use)
    if not rights.ok:
        raise PublishPrepError("rights blocked: " + "; ".join(rights.blockers))
    art = Path(rr["artifact_path"])
    man = Path(rr["manifest_path"])
    if not art.exists() or not man.exists():
        raise PublishPrepError("artifact/manifest file missing")
    package, package_hash = build_package(
        video_id=int(rr["video_id"]), render_run_id=render_run_id,
        artifact_hash=sha256_file(art), manifest_hash=sha256_file(man),
        destination=destination, action=action, privacy=privacy,
        title=title, description=description, asset_permission_refs=asset_ids or [],
        qa_report_id=conn.execute(
            "SELECT id FROM qa_reports WHERE render_run_id=? ORDER BY id DESC LIMIT 1",
            (render_run_id,)).fetchone()["id"],
    )
    with immediate_tx(conn):
        pkg_id = store_package(conn, video_id=int(rr["video_id"]), render_run_id=render_run_id,
                               destination=destination, action=action, privacy=privacy,
                               package=package, package_hash=package_hash)
    return {"ok": True, "package_id": pkg_id, "package_hash": package_hash, "action": action,
            "destination": destination, "note": "local immutable package only; no upload/send/approval execution"}
