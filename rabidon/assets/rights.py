from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from rabidon.utils.timeutil import utc_now_iso

USES = {
    "local_preview", "external_preview", "final_render",
    "private_upload", "public_release", "client_delivery", "portfolio",
}


@dataclass(frozen=True)
class RightsDecision:
    ok: bool
    blockers: list[str]


def _now() -> str:
    return utc_now_iso()


def register_asset(conn: sqlite3.Connection, *, asset_type: str, local_path: str,
                   content_hash: str, owner: str | None = None,
                   provenance: str | None = None, mime_type: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO assets(asset_type,local_path,owner,provenance,content_hash,mime_type,created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (asset_type, local_path, owner, provenance, content_hash, mime_type, _now()),
    )
    return int(cur.lastrowid)


def add_permission(conn: sqlite3.Connection, *, asset_id: int, rights_basis: str,
                   rights_status: str, permitted_uses: list[str], evidence_ref: str | None = None,
                   attribution: str | None = None, expires_at: str | None = None,
                   reviewer: str | None = None) -> int:
    bad = [u for u in permitted_uses if u not in USES]
    if bad:
        raise ValueError(f"unknown permitted uses: {bad}")
    now = _now()
    cur = conn.execute(
        """INSERT INTO asset_permissions(asset_id,rights_basis,rights_status,permitted_uses_json,evidence_ref,attribution,expires_at,reviewer,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (asset_id, rights_basis, rights_status, json.dumps(sorted(set(permitted_uses))),
         evidence_ref, attribution, expires_at, reviewer, now, now),
    )
    return int(cur.lastrowid)


def check_assets_for_use(conn: sqlite3.Connection, asset_ids: list[int], use: str,
                         now_iso: str | None = None) -> RightsDecision:
    if use not in USES:
        raise ValueError(f"unknown use: {use}")
    now = now_iso or _now()
    blockers: list[str] = []
    for aid in sorted(set(asset_ids)):
        row = conn.execute(
            """SELECT p.rights_basis, p.rights_status, p.permitted_uses_json, p.expires_at
               FROM asset_permissions p WHERE p.asset_id=? ORDER BY p.id DESC LIMIT 1""",
            (aid,),
        ).fetchone()
        if not row:
            blockers.append(f"asset:{aid}: no permission record")
            continue
        basis = row["rights_basis"]
        status = row["rights_status"]
        if basis == "unknown" or status in ("pending", "rejected", "expired"):
            blockers.append(f"asset:{aid}: basis={basis} status={status}")
            continue
        expires = row["expires_at"]
        if expires and expires <= now:
            blockers.append(f"asset:{aid}: expired at {expires}")
            continue
        uses = json.loads(row["permitted_uses_json"])
        if use not in uses:
            blockers.append(f"asset:{aid}: use {use} not permitted")
    return RightsDecision(ok=not blockers, blockers=blockers)
