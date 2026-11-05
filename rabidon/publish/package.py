from __future__ import annotations

import json
import sqlite3
from typing import Any

from rabidon.utils.hashing import sha256_json
from rabidon.utils.timeutil import utc_now_iso


def build_package(*, video_id: int, render_run_id: int, artifact_hash: str, manifest_hash: str,
                  destination: str, action: str, privacy: str, title: str,
                  description: str = "", caption_hash: str | None = None,
                  asset_permission_refs: list[int] | None = None,
                  qa_report_id: int | None = None) -> tuple[dict[str, Any], str]:
    # ADR-003: NO approval refs inside package. Approvals reference package_hash.
    package = {
        "schema_version": 1,
        "video_id": video_id,
        "render_run_id": render_run_id,
        "artifact_hash": artifact_hash,
        "manifest_hash": manifest_hash,
        "destination": {"platform": destination},
        "action": action,
        "privacy": privacy,
        "title": title,
        "description": description,
        "caption_hash": caption_hash,
        "required_attributions": [],
        "asset_permission_refs": asset_permission_refs or [],
        "qa_report_id": qa_report_id,
    }
    return package, sha256_json(package)


def store_package(conn: sqlite3.Connection, *, video_id: int, render_run_id: int,
                  destination: str, action: str, privacy: str, package: dict[str, Any],
                  package_hash: str) -> int:
    cur = conn.execute(
        """INSERT INTO publish_packages(video_id,render_run_id,destination,action,privacy,package_json,package_hash,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (video_id, render_run_id, destination, action, privacy,
         json.dumps(package, ensure_ascii=False, sort_keys=True), package_hash, utc_now_iso()),
    )
    return int(cur.lastrowid)
