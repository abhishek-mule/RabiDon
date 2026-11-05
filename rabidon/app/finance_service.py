from __future__ import annotations

import sqlite3


def invoice_collected_summary(conn: sqlite3.Connection, *, client_id: int | None = None) -> dict:
    # Integer paise only (ADR-008). Collected = sum of payment allocations (partial-safe).
    where = "WHERE i.client_id=?" if client_id is not None else ""
    args = (client_id,) if client_id is not None else ()
    inv = conn.execute(
        f"SELECT COALESCE(SUM(amount_paise),0) AS invoiced_paise, COUNT(*) AS invoice_count FROM invoices i {where}",
        args,
    ).fetchone()
    paid = conn.execute(
        f"""SELECT COALESCE(SUM(a.amount_paise),0) AS allocated_paise
            FROM payment_allocations a
            JOIN invoices i ON i.id=a.invoice_id {where}""",
        args,
    ).fetchone()
    invoiced = int(inv["invoiced_paise"])
    allocated = int(paid["allocated_paise"])
    return {
        "invoiced_paise": invoiced,
        "allocated_paise": allocated,
        "outstanding_paise": max(0, invoiced - allocated),
        "invoice_count": int(inv["invoice_count"]),
    }
