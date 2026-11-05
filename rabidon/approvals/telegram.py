from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Protocol

from rabidon.approvals.service import ApprovalOutcome, decide
from rabidon.assets.rights import check_assets_for_use
from rabidon.db.connection import immediate_tx
from rabidon.utils.timeutil import utc_now_iso


class TelegramTransport(Protocol):
    def send_preview(self, *, chat_id: str, text: str, artifact_path: str | None) -> str:
        """Send preview; return message reference. MUST be mocked in tests/offline."""
        ...


@dataclass(frozen=True)
class PreviewGateResult:
    ok: bool
    blockers: list[str]
    message_ref: str | None = None


def _allowed_chat(chat_id: str, allowed_chat_id: str | None) -> bool:
    return not allowed_chat_id or str(chat_id) == str(allowed_chat_id)


def _allowed_approver(approver: str, allowed_user_ids: list[str], chat_id: str,
                      allowed_chat_id: str | None) -> bool:
    uid = approver.replace("tg:", "", 1)
    if allowed_user_ids and uid not in set(allowed_user_ids):
        return False
    return _allowed_chat(chat_id, allowed_chat_id)


def gate_and_send_preview(
    conn: sqlite3.Connection,
    *,
    transport: TelegramTransport,
    chat_id: str,
    allowed_chat_id: str | None,
    asset_ids: list[int],
    preview_text: str,
    artifact_path: str | None = None,
    is_client_confidential: bool = False,
    has_sharing_permission: bool = False,
    request_ref: str | None = None,
) -> PreviewGateResult:
    # ADR-005/C-03: Telegram preview is external transmission.
    blockers: list[str] = []
    if not _allowed_chat(chat_id, allowed_chat_id):
        blockers.append("chat not allowed")
    rights = check_assets_for_use(conn, asset_ids, "external_preview")
    if not rights.ok:
        blockers.extend(rights.blockers)
    if not has_sharing_permission:
        blockers.append("external preview requires sharing permission record")
    if is_client_confidential and not has_sharing_permission:
        # explicit (kept even if redundant) for clarity
        blockers.append("client confidential material requires explicit sharing permission")
    if blockers:
        with immediate_tx(conn):
            conn.execute(
                "INSERT INTO audit_events(actor,action,object_type,object_id,after_json,created_at) VALUES (?,?,?,?,?,?)",
                ("system", "telegram_preview.blocked", "preview", request_ref,
                 json.dumps({"blockers": blockers}, ensure_ascii=False, sort_keys=True),
                 utc_now_iso()),
            )
        return PreviewGateResult(False, blockers)
    ref = transport.send_preview(chat_id=chat_id, text=preview_text, artifact_path=artifact_path)
    with immediate_tx(conn):
        conn.execute(
            "INSERT INTO audit_events(actor,action,object_type,object_id,after_json,created_at) VALUES (?,?,?,?,?,?)",
            ("system", "telegram_preview.sent", "preview", request_ref,
             json.dumps({"chat_id": chat_id, "message_ref": ref}, ensure_ascii=False, sort_keys=True),
             utc_now_iso()),
        )
    return PreviewGateResult(True, [], message_ref=ref)


def handle_callback(
    conn: sqlite3.Connection,
    *,
    token: str,
    approver: str,
    chat_id: str,
    decision: str,
    current_object_hash: str,
    allowed_user_ids: list[str],
    allowed_chat_id: str | None,
) -> ApprovalOutcome:
    if not _allowed_approver(approver, allowed_user_ids, chat_id, allowed_chat_id):
        return ApprovalOutcome(False, "unauthorized", "approver/chat not allowed")
    with immediate_tx(conn):
        return decide(conn, token=token, approver=approver, decision=decision,
                      current_object_hash=current_object_hash)
