from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import business
from rabidon.utils.hashing import sha256_text


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_opt_out_blocks_send_gate(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            lid = business.create_lead(c, source="manual", handle="@x",
                                        contact_provenance="profile")
            did = business.create_outreach_draft(c, lead_id=lid, observation="posted 3 shorts",
                                                 message_text="hello")
            ok, _ = business.can_send_outreach(c, lead_id=lid, draft_id=did,
                                               approved_hash=sha256_text("hello"))
            assert ok is True
            business.set_opt_out(c, lead_id=lid, opt_out=True)
            ok2, reason = business.can_send_outreach(c, lead_id=lid, draft_id=did,
                                                     approved_hash=sha256_text("hello"))
        assert ok2 is False
        assert reason == "lead opted out"
    finally:
        c.close()


def test_outreach_requires_observation_and_exact_approved_hash(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            lid = business.create_lead(c, source="manual")
            with pytest.raises(ValueError):
                business.create_outreach_draft(c, lead_id=lid, observation=" ", message_text="m")
            did = business.create_outreach_draft(c, lead_id=lid, observation="active channel",
                                                 message_text="m1")
            ok, reason = business.can_send_outreach(c, lead_id=lid, draft_id=did,
                                                    approved_hash=sha256_text("m2"))
        assert ok is False
        assert "exact approved" in (reason or "")
    finally:
        c.close()


def test_payment_allocations_use_paise_and_prevent_overallocation(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            cid = business.create_client(c, name="Client A", rate_paise=499900)
            iid = business.create_invoice(c, client_id=cid, amount_paise=499900)
            pid = business.record_payment(c, amount_paise=200000, allocations=[(iid, 200000)])
            assert pid > 0
            with pytest.raises(ValueError):
                business.record_payment(c, amount_paise=100, allocations=[(iid, 101)])
        row = c.execute("SELECT amount_paise FROM payment_allocations WHERE invoice_id=?",
                        (iid,)).fetchone()
        assert int(row["amount_paise"]) == 200000
    finally:
        c.close()


def test_client_project_isolation_records(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            a = business.create_client(c, name="A")
            b = business.create_client(c, name="B")
            pa = business.create_project(c, client_id=a, title="A1", confidentiality="confidential")
            pb = business.create_project(c, client_id=b, title="B1")
        ra = c.execute("SELECT client_id, confidentiality FROM projects WHERE id=?", (pa,)).fetchone()
        rb = c.execute("SELECT client_id FROM projects WHERE id=?", (pb,)).fetchone()
        assert ra["client_id"] == a and ra["confidentiality"] == "confidential"
        assert rb["client_id"] == b
    finally:
        c.close()
