from dataclasses import dataclass
from pathlib import Path

from rabidon.approvals.service import create_request
from rabidon.approvals.telegram import gate_and_send_preview, handle_callback
from rabidon.assets.rights import add_permission, register_asset
from rabidon.db import connect, immediate_tx, migrate


@dataclass
class MockTransport:
    sent: list[dict]
    def send_preview(self, *, chat_id: str, text: str, artifact_path: str | None) -> str:
        self.sent.append({"chat_id": chat_id, "text": text, "artifact_path": artifact_path})
        return "msg:1"


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def _approved_asset(c, use="external_preview"):
    aid = register_asset(c, asset_type="graphic", local_path="x.png", content_hash="sha256:x")
    add_permission(c, asset_id=aid, rights_basis="owned", rights_status="approved",
                   permitted_uses=[use, "local_preview"])
    return aid


def test_external_preview_blocked_without_sharing_permission(tmp_path: Path):
    c = _db(tmp_path)
    t = MockTransport([])
    try:
        with immediate_tx(c):
            aid = _approved_asset(c)
        res = gate_and_send_preview(c, transport=t, chat_id="123", allowed_chat_id="123",
                                    asset_ids=[aid], preview_text="hi",
                                    has_sharing_permission=False)
        assert res.ok is False
        assert any("sharing permission" in b for b in res.blockers)
        assert t.sent == []
    finally:
        c.close()


def test_external_preview_blocked_for_unknown_rights_even_with_sharing(tmp_path: Path):
    c = _db(tmp_path)
    t = MockTransport([])
    try:
        with immediate_tx(c):
            aid = register_asset(c, asset_type="graphic", local_path="x.png",
                                 content_hash="sha256:x")
            add_permission(c, asset_id=aid, rights_basis="unknown", rights_status="pending",
                           permitted_uses=["local_preview"])
        res = gate_and_send_preview(c, transport=t, chat_id="123", allowed_chat_id="123",
                                    asset_ids=[aid], preview_text="hi",
                                    has_sharing_permission=True)
        assert res.ok is False
        assert t.sent == []
    finally:
        c.close()


def test_external_preview_sends_when_rights_and_sharing_ok(tmp_path: Path):
    c = _db(tmp_path)
    t = MockTransport([])
    try:
        with immediate_tx(c):
            aid = _approved_asset(c)
        res = gate_and_send_preview(c, transport=t, chat_id="123", allowed_chat_id="123",
                                    asset_ids=[aid], preview_text="hi",
                                    has_sharing_permission=True)
        assert res.ok is True
        assert t.sent and t.sent[0]["chat_id"] == "123"
    finally:
        c.close()


def test_callback_rejects_wrong_user_and_chat(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            req = create_request(c, action="telegram_preview", object_type="render_run",
                                 object_id="1", object_version="v1", object_hash="sha256:a")
        bad_user = handle_callback(c, token=req.token, approver="tg:999", chat_id="123",
                                   decision="approved", current_object_hash="sha256:a",
                                   allowed_user_ids=["42"], allowed_chat_id="123")
        bad_chat = handle_callback(c, token=req.token, approver="tg:42", chat_id="999",
                                   decision="approved", current_object_hash="sha256:a",
                                   allowed_user_ids=["42"], allowed_chat_id="123")
        ok = handle_callback(c, token=req.token, approver="tg:42", chat_id="123",
                             decision="approved", current_object_hash="sha256:a",
                             allowed_user_ids=["42"], allowed_chat_id="123")
        assert bad_user.status == "unauthorized"
        assert bad_chat.status == "unauthorized"
        assert ok.ok is True
    finally:
        c.close()
