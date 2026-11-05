from pathlib import Path

import pytest

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_unsupported_factual_blocks_script_approval(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="T", angle="A", format="commentary")
            cid, _ = editorial.add_claim(c, topic_id=tid, text="bad fact",
                                         evidence_status="unsupported")
            # Even if someone tries to review, gate must block unsupported status.
            editorial.review_claim(c, claim_id=cid, claim_revision_id=1,
                                   decision="accepted", reviewer="tester",
                                   accepted_wording="bad fact")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="script",
                                                 claim_ids=[cid])
            gate = editorial.approve_script_revision(c, script_revision_id=srev,
                                                     reviewer="tester")
        assert gate.ok is False
        assert any("evidence_status=unsupported" in b for b in gate.blockers)
        status = c.execute("SELECT approval_status FROM script_revisions WHERE id=?",
                           (srev,)).fetchone()[0]
        assert status == "blocked"
    finally:
        c.close()


def test_evidence_change_invalidates_factual_review(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="T", angle="A", format="commentary")
            src = editorial.add_source(c, title="S", source_type="primary",
                                       accessed_at="2026-11-05T00:00:00+00:00")
            cid, rev1 = editorial.add_claim(c, topic_id=tid, text="fact",
                                            evidence_status="supported",
                                            source_ids=[src])
            editorial.review_claim(c, claim_id=cid, claim_revision_id=rev1,
                                   decision="accepted", reviewer="tester",
                                   accepted_wording="fact")
            _sid, srev = editorial.create_script(c, topic_id=tid, text="script",
                                                 claim_ids=[cid])
            ok_gate = editorial.approve_script_revision(c, script_revision_id=srev,
                                                        reviewer="tester")
        assert ok_gate.ok is True

        with immediate_tx(c):
            # New revision/evidence hash -> prior acceptance no longer valid.
            editorial.add_claim_revision(c, claim_id=cid, text="fact changed",
                                         evidence_status="supported", source_ids=[src])
            _sid2, srev2 = editorial.create_script(c, topic_id=tid, text="script2",
                                                   claim_ids=[cid])
            gate = editorial.approve_script_revision(c, script_revision_id=srev2,
                                                     reviewer="tester")
        assert gate.ok is False
        assert any("no valid human acceptance" in b for b in gate.blockers)
    finally:
        c.close()


def test_supported_claim_requires_human_acceptance(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            tid = editorial.create_topic(c, title="T", angle="A", format="commentary")
            src = editorial.add_source(c, title="S", source_type="primary",
                                       accessed_at="2026-11-05T00:00:00+00:00")
            cid, _ = editorial.add_claim(c, topic_id=tid, text="fact",
                                         evidence_status="supported", source_ids=[src])
            _sid, srev = editorial.create_script(c, topic_id=tid, text="script",
                                                 claim_ids=[cid])
            gate = editorial.approve_script_revision(c, script_revision_id=srev,
                                                     reviewer="tester")
        assert gate.ok is False
    finally:
        c.close()
