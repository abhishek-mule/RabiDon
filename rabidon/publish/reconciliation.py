from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Protocol

from rabidon.db.connection import immediate_tx
from rabidon.utils.timeutil import utc_now_iso


class PublisherProbe(Protocol):
    def lookup(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> dict:
        """Return observed state. MUST be mocked in offline tests. No blind upload."""
        ...


@dataclass(frozen=True)
class ReconcileResult:
    local_state: str
    remote_id: str | None
    detail: str


def mark_attempt_started(conn: sqlite3.Connection, *, destination: str, action: str,
                         idempotency_key: str, publish_package_id: int | None = None) -> int:
    now = utc_now_iso()
    with immediate_tx(conn):
        row = conn.execute(
            "SELECT id FROM publication_attempts WHERE destination=? AND action=? AND idempotency_key=?",
            (destination, action, idempotency_key),
        ).fetchone()
        if row:
            return int(row["id"])
        cur = conn.execute(
            """INSERT INTO publication_attempts(publish_package_id,destination,action,idempotency_key,local_state,created_at,updated_at)
               VALUES (?,?,?,?,'uploading',?,?)""",
            (publish_package_id, destination, action, idempotency_key, now, now),
        )
        return int(cur.lastrowid)


def mark_ambiguous(conn: sqlite3.Connection, *, attempt_id: int, error: str | None = None) -> None:
    # ADR-007: never blind retry.
    with immediate_tx(conn):
        conn.execute(
            "UPDATE publication_attempts SET local_state='reconciliation_required', error=?, updated_at=? WHERE id=?",
            (error, utc_now_iso(), attempt_id),
        )


def reconcile(conn: sqlite3.Connection, *, attempt_id: int, probe: PublisherProbe) -> ReconcileResult:
    row = conn.execute("SELECT * FROM publication_attempts WHERE id=?", (attempt_id,)).fetchone()
    if not row:
        raise ValueError("attempt not found")
    obs = probe.lookup(destination=row["destination"], idempotency_key=row["idempotency_key"],
                       remote_id=row["remote_id"])
    remote_id = obs.get("remote_id") or row["remote_id"]
    # Conservative: if probe cannot confirm, keep reconciliation_required.
    if obs.get("state") == "uploaded":
        local = "uploaded"
        detail = "remote upload confirmed"
    elif obs.get("state") == "not_found":
        local = "failed" if row["local_state"] != "uploaded" else "reconciliation_required"
        detail = "remote object not found"
    else:
        local = "reconciliation_required"
        detail = obs.get("detail") or "ambiguous; operator review required"
    with immediate_tx(conn):
        conn.execute(
            """UPDATE publication_attempts SET local_state=?, remote_id=?, remote_url=?,
               processing_state=?, visibility_state=?, last_observed_at=?, updated_at=?
               WHERE id=?""",
            (local, remote_id, obs.get("remote_url"), obs.get("processing_state", "unknown"),
             obs.get("visibility_state", "unknown"), utc_now_iso(), utc_now_iso(), attempt_id),
        )
    return ReconcileResult(local, remote_id, detail)
