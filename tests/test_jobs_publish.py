from dataclasses import dataclass
from pathlib import Path

from rabidon.db import connect, migrate
from rabidon.jobs.queue import claim_next, complete, enqueue, heartbeat
from rabidon.publish.reconciliation import mark_ambiguous, mark_attempt_started, reconcile


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_job_claim_requires_matching_owner_token(tmp_path: Path):
    c = _db(tmp_path)
    try:
        jid = enqueue(c, job_type="render", payload={"x": 1})
        claimed = claim_next(c, worker_id="w1", lease_seconds=300)
        assert claimed and claimed.id == jid
        assert heartbeat(c, job_id=jid, worker_token=claimed.worker_token)
        assert heartbeat(c, job_id=jid, worker_token="bad") is False
        assert complete(c, job_id=jid, worker_token="bad", status="succeeded") is False
        assert complete(c, job_id=jid, worker_token=claimed.worker_token, status="succeeded") is True
    finally:
        c.close()


@dataclass
class Probe:
    response: dict
    def lookup(self, *, destination, idempotency_key, remote_id):
        return self.response


def test_ambiguous_upload_enters_reconciliation_required(tmp_path: Path):
    c = _db(tmp_path)
    try:
        aid = mark_attempt_started(c, destination="youtube", action="private_upload",
                                   idempotency_key="k1")
        mark_ambiguous(c, attempt_id=aid, error="network timeout after send")
        row = c.execute("SELECT local_state FROM publication_attempts WHERE id=?",
                        (aid,)).fetchone()
        assert row["local_state"] == "reconciliation_required"
        res = reconcile(c, attempt_id=aid, probe=Probe({"state": "unknown"}))
        assert res.local_state == "reconciliation_required"
        res2 = reconcile(c, attempt_id=aid, probe=Probe({"state": "uploaded", "remote_id": "yt1"}))
        assert res2.local_state == "uploaded"
        assert res2.remote_id == "yt1"
    finally:
        c.close()
