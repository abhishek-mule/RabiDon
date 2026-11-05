from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from rabidon.utils.hashing import sha256_text
from rabidon.utils.timeutil import utc_now_iso


@dataclass(frozen=True)
class ApprovalRequestView:
    request_id: int
    token: str  # returned once to caller; only hash stored


@dataclass(frozen=True)
class ApprovalOutcome:
    ok: bool
    status: str
    reason: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def create_request(conn: sqlite3.Connection, *, action: str, object_type: str,
                   object_id: str, object_version: str, object_hash: str,
                   target: dict | None = None, ttl_seconds: int = 3600) -> ApprovalRequestView:
    token = secrets.token_urlsafe(32)
    token_hash = sha256_text(token)
    now = _now()
    cur = conn.execute(
        """INSERT INTO approval_requests(action,object_type,object_id,object_version,object_hash,target_json,token_hash,status,expires_at,created_at)
           VALUES (?,?,?,?,?,?,?,'pending',?,?)""",
        (action, object_type, str(object_id), object_version, object_hash,
         json.dumps(target or {}, sort_keys=True), token_hash, _iso(now + timedelta(seconds=ttl_seconds)), _iso(now)),
    )
    return ApprovalRequestView(request_id=int(cur.lastrowid), token=token)


def decide(conn: sqlite3.Connection, *, token: str, approver: str, decision: str,
           current_object_hash: str, notes: str | None = None) -> ApprovalOutcome:
    token_hash = sha256_text(token)
    row = conn.execute(
        "SELECT * FROM approval_requests WHERE token_hash=?",
        (token_hash,),
    ).fetchone()
    if not row:
        return ApprovalOutcome(False, "not_found", "request not found")
    status = row["status"]
    if status != "pending":
        # Duplicate/consumed/expired callbacks are harmless.
        return ApprovalOutcome(False, status, "request not pending")
    if row["expires_at"] <= utc_now_iso():
        conn.execute("UPDATE approval_requests SET status='expired' WHERE id=?", (row["id"],))
        return ApprovalOutcome(False, "expired", "request expired")
    if row["object_hash"] != current_object_hash:
        conn.execute("UPDATE approval_requests SET status='expired' WHERE id=?", (row["id"],))
        return ApprovalOutcome(False, "hash_mismatch", "object changed; approval invalidated")
    if decision not in ("approved", "rejected", "changes_requested"):
        return ApprovalOutcome(False, "invalid_decision", "invalid decision")
    new_status = "consumed" if decision == "approved" else decision
    conn.execute("UPDATE approval_requests SET status=? WHERE id=? AND status='pending'",
                 (new_status, row["id"]))
    conn.execute(
        "INSERT INTO approval_decisions(request_id,approver,decision,notes,created_at) VALUES (?,?,?,?,?)",
        (row["id"], approver, decision, notes, utc_now_iso()),
    )
    return ApprovalOutcome(True, new_status)
