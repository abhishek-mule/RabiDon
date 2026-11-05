from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from rabidon.db.connection import immediate_tx
from rabidon.utils.timeutil import utc_now_iso


@dataclass(frozen=True)
class ClaimedJob:
    id: int
    job_type: str
    payload: dict
    worker_token: str
    attempts: int


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def enqueue(conn: sqlite3.Connection, *, job_type: str, payload: dict | None = None,
            idempotency_key: str | None = None, max_attempts: int = 3,
            run_after_iso: str | None = None) -> int:
    now = utc_now_iso()
    with immediate_tx(conn):
        if idempotency_key:
            row = conn.execute("SELECT id FROM jobs WHERE idempotency_key=?",
                               (idempotency_key,)).fetchone()
            if row:
                return int(row["id"])
        cur = conn.execute(
            """INSERT INTO jobs(job_type,payload_json,idempotency_key,status,max_attempts,run_after,created_at,updated_at)
               VALUES (?,?,?, 'queued',?,?,?,?)""",
            (job_type, json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
             idempotency_key, max_attempts, run_after_iso or now, now, now),
        )
        return int(cur.lastrowid)


def claim_next(conn: sqlite3.Connection, *, worker_id: str, lease_seconds: int = 300) -> ClaimedJob | None:
    now = _now()
    now_iso = _iso(now)
    token = secrets.token_urlsafe(18)
    with immediate_tx(conn):
        # Recover expired leases.
        conn.execute(
            """UPDATE jobs SET status='queued', locked_by=NULL, worker_token=NULL,
                               locked_at=NULL, heartbeat_at=NULL, lease_expires_at=NULL,
                               updated_at=?
               WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?""",
            (now_iso, now_iso),
        )
        row = conn.execute(
            """SELECT id, job_type, payload_json, attempts, max_attempts
               FROM jobs WHERE status='queued' AND run_after <= ?
               ORDER BY id ASC LIMIT 1""",
            (now_iso,),
        ).fetchone()
        if not row:
            return None
        lease = _iso(now + timedelta(seconds=lease_seconds))
        updated = conn.execute(
            """UPDATE jobs SET status='running', locked_by=?, worker_token=?, locked_at=?,
                               heartbeat_at=?, lease_expires_at=?, attempts=attempts+1, updated_at=?
               WHERE id=? AND status='queued'""",
            (worker_id, token, now_iso, now_iso, lease, now_iso, row["id"]),
        )
        if updated.rowcount != 1:
            return None
        return ClaimedJob(id=int(row["id"]), job_type=row["job_type"],
                          payload=json.loads(row["payload_json"]),
                          worker_token=token, attempts=int(row["attempts"]) + 1)


def heartbeat(conn: sqlite3.Connection, *, job_id: int, worker_token: str,
              lease_seconds: int = 300) -> bool:
    now = _now()
    with immediate_tx(conn):
        cur = conn.execute(
            """UPDATE jobs SET heartbeat_at=?, lease_expires_at=?, updated_at=?
               WHERE id=? AND status='running' AND worker_token=?""",
            (_iso(now), _iso(now + timedelta(seconds=lease_seconds)), _iso(now),
             job_id, worker_token),
        )
        return cur.rowcount == 1


def complete(conn: sqlite3.Connection, *, job_id: int, worker_token: str,
             status: str, error: str | None = None,
             run_after_iso: str | None = None) -> bool:
    if status not in ("succeeded", "retry_scheduled", "awaiting_approval",
                      "awaiting_manual_input", "failed", "dead", "queued"):
        raise ValueError("invalid completion status")
    now = utc_now_iso()
    with immediate_tx(conn):
        row = conn.execute("SELECT attempts, max_attempts FROM jobs WHERE id=? AND worker_token=?",
                           (job_id, worker_token)).fetchone()
        if not row:
            return False
        final = status
        if status == "retry_scheduled":
            final = "dead" if int(row["attempts"]) >= int(row["max_attempts"]) else "queued"
        cur = conn.execute(
            """UPDATE jobs SET status=?, locked_by=NULL, worker_token=NULL, locked_at=NULL,
                               heartbeat_at=NULL, lease_expires_at=?, last_error=?,
                               run_after=COALESCE(?, run_after), updated_at=?
               WHERE id=? AND worker_token=? AND status='running'""",
            (final, None, error, run_after_iso, now, job_id, worker_token),
        )
        return cur.rowcount == 1
