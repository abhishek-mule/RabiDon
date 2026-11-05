from pathlib import Path

from rabidon.db import connect, migrate
from rabidon.jobs.queue import enqueue
from rabidon.jobs.worker import run_once


def test_worker_dispatch_and_completion(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        jid = enqueue(c, job_type="echo", payload={"ok": 1})
        def handler(conn, job):
            assert job.payload["ok"] == 1
            return "succeeded", None
        res = run_once(c, worker_id="w1", handlers={"echo": handler})
        assert res and res.job_id == jid and res.status == "succeeded"
        row = c.execute("SELECT status, worker_token FROM jobs WHERE id=?", (jid,)).fetchone()
        assert row["status"] == "succeeded"
        assert row["worker_token"] is None
    finally:
        c.close()


def test_worker_missing_handler_fails_job(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        jid = enqueue(c, job_type="unknown", payload={})
        res = run_once(c, worker_id="w1", handlers={})
        assert res and res.status == "failed"
        row = c.execute("SELECT status, last_error FROM jobs WHERE id=?", (jid,)).fetchone()
        assert row["status"] == "failed"
        assert "no handler" in row["last_error"]
    finally:
        c.close()
