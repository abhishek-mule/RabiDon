"""DB-backed publish attempt flow (mock/offline). No upload/send execution."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from rabidon.approvals.service import create_request
from rabidon.assets.rights import check_assets_for_use
from rabidon.db.connection import immediate_tx
from rabidon.publish.ports import ProbeObservation, PublisherProbePort, SessionRefStore
from rabidon.publish.reconciliation import mark_attempt_started, reconcile
from rabidon.utils.timeutil import utc_now_iso

PUBLISH_ACTIONS = {"private_upload", "public_release"}
ACTION_USE = {"private_upload": "private_upload", "public_release": "public_release"}


@dataclass(frozen=True)
class AttemptResult:
    ok: bool
    attempt_id: int | None = None
    local_state: str | None = None
    session_ref: str | None = None
    error: str | None = None
    approval_request_id: int | None = None
    approval_token: str | None = None


def _pkg(conn: sqlite3.Connection, publish_package_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM publish_packages WHERE id=?", (publish_package_id,)).fetchone()
    if not row:
        raise ValueError("publish package not found")
    return row


def create_publish_approval(conn: sqlite3.Connection, *, publish_package_id: int,
                            approver_target: dict | None = None) -> AttemptResult:
    pkg = _pkg(conn, publish_package_id)
    action = pkg["action"]
    if action not in PUBLISH_ACTIONS:
        return AttemptResult(False, error=f"action not approvable for publish: {action}")
    with immediate_tx(conn):
        req = create_request(conn, action=action, object_type="publish_package",
                             object_id=str(publish_package_id), object_version="v1",
                             object_hash=pkg["package_hash"], target=approver_target)
    return AttemptResult(True, approval_request_id=req.request_id, approval_token=req.token)


def execute_mock_attempt(conn: sqlite3.Connection, *, publish_package_id: int,
                         action: str, destination: str, idempotency_key: str,
                         asset_ids: list[int], adapter: PublisherProbePort,
                         session_store: SessionRefStore | None = None,
                         approved_action: str | None = None,
                         approved_package_hash: str | None = None,
                         mock_remote_id: str | None = None,
                         simulate_ambiguous: bool = False) -> AttemptResult:
    # ADR-004/007: exact action+package approval binding required for external intent;
    # this mock flow never performs network upload.
    if action not in PUBLISH_ACTIONS:
        return AttemptResult(False, error="invalid publish action")
    pkg = _pkg(conn, publish_package_id)
    if pkg["action"] != action or pkg["destination"] != destination:
        return AttemptResult(False, error="package action/destination mismatch")
    if approved_action != action or approved_package_hash != pkg["package_hash"]:
        return AttemptResult(False, error="exact approval (action+package hash) required")
    rights = check_assets_for_use(conn, asset_ids, ACTION_USE[action])
    if not rights.ok:
        return AttemptResult(False, error="rights blocked: " + "; ".join(rights.blockers))

    attempt_id = mark_attempt_started(conn, destination=destination, action=action,
                                      idempotency_key=idempotency_key,
                                      publish_package_id=publish_package_id)
    session_ref = None
    if session_store is not None and hasattr(adapter, "prepare_session"):
        raw = adapter.prepare_session(package_hash=pkg["package_hash"], destination=destination, action=action)  # type: ignore[attr-defined]
        session_ref = session_store.put(attempt_id, raw)
        with immediate_tx(conn):
            conn.execute("UPDATE publication_attempts SET upload_session_ref=?, updated_at=? WHERE id=?",
                         (session_ref, utc_now_iso(), attempt_id))

    if simulate_ambiguous:
        with immediate_tx(conn):
            conn.execute("UPDATE publication_attempts SET local_state='reconciliation_required', updated_at=? WHERE id=?",
                         (utc_now_iso(), attempt_id))
        return AttemptResult(True, attempt_id=attempt_id, local_state="reconciliation_required",
                             session_ref=session_ref)

    # Mock "uploaded" observation persisted; no network call.
    obs = ProbeObservation(state="uploaded", remote_id=mock_remote_id or f"mock:{idempotency_key}")
    with immediate_tx(conn):
        conn.execute(
            """UPDATE publication_attempts SET local_state='uploaded', remote_id=?, processing_state=?, visibility_state=?, last_observed_at=?, updated_at=? WHERE id=?""",
            (obs.remote_id, obs.processing_state, obs.visibility_state, utc_now_iso(), utc_now_iso(), attempt_id),
        )
    return AttemptResult(True, attempt_id=attempt_id, local_state="uploaded", session_ref=session_ref)
