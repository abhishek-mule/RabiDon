from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from rabidon.utils.hashing import sha256_json
from rabidon.utils.timeutil import utc_now_iso

EVIDENCE_STATES = {"supported", "partial", "conflicting", "unsupported", "unknown"}


@dataclass(frozen=True)
class ClaimGateResult:
    ok: bool
    blockers: list[str]


def _now() -> str:
    return utc_now_iso()


def create_topic(conn: sqlite3.Connection, *, title: str, angle: str, format: str,
                 audience: str | None = None, priority: int = 5) -> int:
    now = _now()
    cur = conn.execute(
        """INSERT INTO topics(title,angle,audience,format,priority,status,created_at,updated_at)
           VALUES (?,?,?,?,?,'idea',?,?)""",
        (title, angle, audience, format, priority, now, now),
    )
    return int(cur.lastrowid)


def add_source(conn: sqlite3.Connection, *, title: str, source_type: str, accessed_at: str,
               url: str | None = None, reliability: str = "unknown",
               notes: str | None = None, content_hash: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO sources(url,title,source_type,accessed_at,reliability,notes,content_hash,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (url, title, source_type, accessed_at, reliability, notes, content_hash, _now()),
    )
    return int(cur.lastrowid)


def _evidence_hash(evidence_status: str, source_ids: list[int], notes: list[str | None]) -> str:
    return sha256_json({
        "evidence_status": evidence_status,
        "source_ids": sorted(source_ids),
        "notes": notes,
    })


def add_claim(conn: sqlite3.Connection, *, topic_id: int, text: str,
              evidence_status: str = "unknown", source_ids: list[int] | None = None,
              source_notes: list[str | None] | None = None) -> tuple[int, int]:
    if evidence_status not in EVIDENCE_STATES:
        raise ValueError(f"invalid evidence_status: {evidence_status}")
    sids = source_ids or []
    notes = source_notes or [None] * len(sids)
    if len(notes) != len(sids):
        raise ValueError("source_notes length must match source_ids")
    now = _now()
    ev_hash = _evidence_hash(evidence_status, sids, notes)
    cur = conn.execute(
        "INSERT INTO claims(topic_id,created_at,updated_at) VALUES (?,?,?)",
        (topic_id, now, now),
    )
    claim_id = int(cur.lastrowid)
    rev_cur = conn.execute(
        """INSERT INTO claim_revisions(claim_id,revision,text,evidence_status,evidence_hash,created_at)
           VALUES (?,?,?,?,?,?)""",
        (claim_id, 1, text, evidence_status, ev_hash, now),
    )
    rev_id = int(rev_cur.lastrowid)
    for sid, note in zip(sids, notes):
        conn.execute(
            "INSERT INTO claim_revision_sources(claim_revision_id,source_id,supporting_note) VALUES (?,?,?)",
            (rev_id, sid, note),
        )
    conn.execute("UPDATE claims SET current_revision_id=?, updated_at=? WHERE id=?",
                 (rev_id, now, claim_id))
    return claim_id, rev_id


def add_claim_revision(conn: sqlite3.Connection, *, claim_id: int, text: str,
                       evidence_status: str, source_ids: list[int] | None = None,
                       source_notes: list[str | None] | None = None) -> int:
    if evidence_status not in EVIDENCE_STATES:
        raise ValueError(f"invalid evidence_status: {evidence_status}")
    sids = source_ids or []
    notes = source_notes or [None] * len(sids)
    row = conn.execute(
        "SELECT COALESCE(MAX(revision),0) AS n FROM claim_revisions WHERE claim_id=?",
        (claim_id,),
    ).fetchone()
    next_rev = int(row["n"]) + 1
    now = _now()
    ev_hash = _evidence_hash(evidence_status, sids, notes)
    cur = conn.execute(
        """INSERT INTO claim_revisions(claim_id,revision,text,evidence_status,evidence_hash,created_at)
           VALUES (?,?,?,?,?,?)""",
        (claim_id, next_rev, text, evidence_status, ev_hash, now),
    )
    rev_id = int(cur.lastrowid)
    for sid, note in zip(sids, notes):
        conn.execute(
            "INSERT INTO claim_revision_sources(claim_revision_id,source_id,supporting_note) VALUES (?,?,?)",
            (rev_id, sid, note),
        )
    conn.execute("UPDATE claims SET current_revision_id=?, updated_at=? WHERE id=?",
                 (rev_id, now, claim_id))
    return rev_id


def review_claim(conn: sqlite3.Connection, *, claim_id: int, claim_revision_id: int,
                 decision: str, reviewer: str, accepted_wording: str | None = None,
                 notes: str | None = None) -> int:
    rev = conn.execute(
        "SELECT evidence_hash FROM claim_revisions WHERE id=? AND claim_id=?",
        (claim_revision_id, claim_id),
    ).fetchone()
    if not rev:
        raise ValueError("claim revision not found for claim")
    cur = conn.execute(
        """INSERT INTO claim_reviews(claim_id,claim_revision_id,evidence_hash,decision,accepted_wording,reviewer,notes,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (claim_id, claim_revision_id, rev["evidence_hash"], decision,
         accepted_wording, reviewer, notes, _now()),
    )
    return int(cur.lastrowid)


def _latest_valid_acceptance(conn: sqlite3.Connection, claim_id: int) -> sqlite3.Row | None:
    # Acceptance is valid only when bound to current claim revision + current evidence hash.
    row = conn.execute(
        """SELECT cr.id, cr.claim_revision_id, cr.decision, cr.accepted_wording, cr.evidence_hash
           FROM claim_reviews cr
           JOIN claims c ON c.id = cr.claim_id
           JOIN claim_revisions rv ON rv.id = cr.claim_revision_id
           WHERE cr.claim_id = ?
             AND cr.claim_revision_id = c.current_revision_id
             AND cr.evidence_hash = rv.evidence_hash
             AND cr.decision IN ('accepted','narrowed')
           ORDER BY cr.id DESC LIMIT 1""",
        (claim_id,),
    ).fetchone()
    return row


def check_script_claims_for_approval(conn: sqlite3.Connection, claim_ids: list[int]) -> ClaimGateResult:
    blockers: list[str] = []
    for cid in claim_ids:
        claim = conn.execute(
            """SELECT c.id, rv.evidence_status, rv.text
               FROM claims c JOIN claim_revisions rv ON rv.id = c.current_revision_id
               WHERE c.id=?""",
            (cid,),
        ).fetchone()
        if not claim:
            blockers.append(f"claim:{cid}: missing")
            continue
        status = claim["evidence_status"]
        if status in ("unsupported", "unknown"):
            blockers.append(f"claim:{cid}: evidence_status={status}")
            continue
        acceptance = _latest_valid_acceptance(conn, cid)
        if not acceptance:
            blockers.append(f"claim:{cid}: no valid human acceptance for current revision/evidence")
            continue
        if status == "conflicting" and acceptance["decision"] != "narrowed":
            blockers.append(f"claim:{cid}: conflicting evidence requires narrowed acceptance")
    return ClaimGateResult(ok=not blockers, blockers=blockers)


def create_script(conn: sqlite3.Connection, *, topic_id: int, text: str,
                  claim_ids: list[int] | None = None, language: str = "hi-IN") -> tuple[int, int]:
    now = _now()
    cur = conn.execute(
        "INSERT INTO scripts(topic_id,created_at,updated_at) VALUES (?,?,?)",
        (topic_id, now, now),
    )
    script_id = int(cur.lastrowid)
    rev_cur = conn.execute(
        """INSERT INTO script_revisions(script_id,revision,language,text,approval_status,created_at)
           VALUES (?,1,?,?,'draft',?)""",
        (script_id, language, text, now),
    )
    rev_id = int(rev_cur.lastrowid)
    for cid in (claim_ids or []):
        conn.execute(
            "INSERT INTO script_revision_claims(script_revision_id,claim_id) VALUES (?,?)",
            (rev_id, cid),
        )
    conn.execute("UPDATE scripts SET current_revision_id=?, updated_at=? WHERE id=?",
                 (rev_id, now, script_id))
    return script_id, rev_id


def approve_script_revision(conn: sqlite3.Connection, *, script_revision_id: int,
                            reviewer: str) -> ClaimGateResult:
    row = conn.execute(
        "SELECT id, script_id, approval_status FROM script_revisions WHERE id=?",
        (script_revision_id,),
    ).fetchone()
    if not row:
        raise ValueError("script revision not found")
    claim_rows = conn.execute(
        "SELECT claim_id FROM script_revision_claims WHERE script_revision_id=? ORDER BY claim_id",
        (script_revision_id,),
    ).fetchall()
    claim_ids = [int(r["claim_id"]) for r in claim_rows]
    gate = check_script_claims_for_approval(conn, claim_ids)
    if not gate.ok:
        conn.execute(
            "UPDATE script_revisions SET approval_status='blocked' WHERE id=?",
            (script_revision_id,),
        )
        conn.execute(
            "INSERT INTO audit_events(actor,action,object_type,object_id,after_json,created_at) VALUES (?,?,?,?,?,?)",
            (reviewer, "script.approval_blocked", "script_revision", str(script_revision_id),
             '{"blockers":' + str(len(gate.blockers)) + '}', _now()),
        )
        return gate
    conn.execute(
        "UPDATE script_revisions SET approval_status='approved' WHERE id=?",
        (script_revision_id,),
    )
    conn.execute(
        "UPDATE scripts SET current_revision_id=?, updated_at=? WHERE id=(SELECT script_id FROM script_revisions WHERE id=?)",
        (script_revision_id, _now(), script_revision_id),
    )
    conn.execute(
        "INSERT INTO audit_events(actor,action,object_type,object_id,created_at) VALUES (?,?,?,?,?)",
        (reviewer, "script.approved", "script_revision", str(script_revision_id), _now()),
    )
    return gate
