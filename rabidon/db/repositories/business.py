from __future__ import annotations

import sqlite3

from rabidon.utils.hashing import sha256_text
from rabidon.utils.timeutil import utc_now_iso


def _now() -> str:
    return utc_now_iso()


def create_lead(conn: sqlite3.Connection, *, source: str, handle: str | None = None,
                platform: str | None = None, contact_provenance: str | None = None,
                fit_score: int | None = None, notes: str | None = None) -> int:
    now = _now()
    cur = conn.execute(
        """INSERT INTO leads(handle,platform,source,contact_provenance,fit_score,status,opt_out,notes,created_at,updated_at)
           VALUES (?,?,?,?,?,'new',0,?,?,?)""",
        (handle, platform, source, contact_provenance, fit_score, notes, now, now),
    )
    return int(cur.lastrowid)


def set_opt_out(conn: sqlite3.Connection, *, lead_id: int, opt_out: bool) -> None:
    conn.execute("UPDATE leads SET opt_out=?, updated_at=? WHERE id=?",
                 (1 if opt_out else 0, _now(), lead_id))


def create_outreach_draft(conn: sqlite3.Connection, *, lead_id: int, observation: str,
                          message_text: str) -> int:
    if not observation or not observation.strip():
        raise ValueError("genuine relevant observation required")
    lead = conn.execute("SELECT opt_out FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not lead:
        raise ValueError("lead not found")
    # Draft can be created for record, but sending must be separately gated.
    now = _now()
    cur = conn.execute(
        """INSERT INTO outreach_drafts(lead_id,observation,message_text,status,created_at,updated_at)
           VALUES (?,?,?,'draft',?,?)""",
        (lead_id, observation.strip(), message_text, now, now),
    )
    return int(cur.lastrowid)


def can_send_outreach(conn: sqlite3.Connection, *, lead_id: int, draft_id: int,
                      approved_hash: str | None) -> tuple[bool, str | None]:
    lead = conn.execute("SELECT opt_out FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not lead:
        return False, "lead not found"
    if int(lead["opt_out"]) == 1:
        return False, "lead opted out"
    draft = conn.execute("SELECT * FROM outreach_drafts WHERE id=? AND lead_id=?",
                         (draft_id, lead_id)).fetchone()
    if not draft:
        return False, "draft not found"
    if not draft["observation"] or not draft["observation"].strip():
        return False, "observation required"
    expected = sha256_text(draft["message_text"])
    if not approved_hash or approved_hash != expected:
        return False, "exact approved message hash required"
    return True, None


def create_client(conn: sqlite3.Connection, *, name: str, lead_id: int | None = None,
                  package: str | None = None, rate_paise: int | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO clients(lead_id,name,package,rate_paise,created_at) VALUES (?,?,?,?,?)",
        (lead_id, name, package, rate_paise, _now()),
    )
    return int(cur.lastrowid)


def create_project(conn: sqlite3.Connection, *, client_id: int, title: str,
                   confidentiality: str = "normal") -> int:
    cur = conn.execute(
        "INSERT INTO projects(client_id,title,confidentiality,created_at) VALUES (?,?,?,?)",
        (client_id, title, confidentiality, _now()),
    )
    return int(cur.lastrowid)


def create_invoice(conn: sqlite3.Connection, *, client_id: int, amount_paise: int,
                   project_id: int | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO invoices(client_id,project_id,amount_paise,status,issued_at) VALUES (?,?,?,'due',?)",
        (client_id, project_id, amount_paise, _now()),
    )
    return int(cur.lastrowid)


def record_payment(conn: sqlite3.Connection, *, amount_paise: int,
                   allocations: list[tuple[int, int]], method: str | None = None,
                   reference: str | None = None) -> int:
    # allocations: [(invoice_id, amount_paise)] - supports partial payments.
    total_alloc = sum(a for _, a in allocations)
    if total_alloc > amount_paise:
        raise ValueError("allocations exceed payment amount")
    cur = conn.execute(
        "INSERT INTO payments(amount_paise,paid_at,method,reference) VALUES (?,?,?,?)",
        (amount_paise, _now(), method, reference),
    )
    pid = int(cur.lastrowid)
    for inv_id, amt in allocations:
        conn.execute(
            "INSERT INTO payment_allocations(payment_id,invoice_id,amount_paise,created_at) VALUES (?,?,?,?)",
            (pid, inv_id, amt, _now()),
        )
    return pid
