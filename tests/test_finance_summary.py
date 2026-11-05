from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import business
from rabidon.app.finance_service import invoice_collected_summary


def test_finance_summary_uses_paise_allocations(tmp_path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        with immediate_tx(c):
            cid = business.create_client(c, name="C")
            iid = business.create_invoice(c, client_id=cid, amount_paise=50000)
            business.record_payment(c, amount_paise=20000, allocations=[(iid, 20000)])
        s = invoice_collected_summary(c, client_id=cid)
        assert s["invoiced_paise"] == 50000
        assert s["allocated_paise"] == 20000
        assert s["outstanding_paise"] == 30000
    finally:
        c.close()
