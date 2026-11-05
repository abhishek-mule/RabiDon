from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable

from rabidon.jobs.queue import ClaimedJob, claim_next, complete
from rabidon.utils.timeutil import utc_now_iso


Handler = Callable[[sqlite3.Connection, ClaimedJob], tuple[str, str | None]]
# returns (status, error) where status is accepted by complete()


@dataclass
class WorkerResult:
    job_id: int
    status: str
    error: str | None = None


def run_once(conn: sqlite3.Connection, *, worker_id: str, handlers: dict[str, Handler],
             lease_seconds: int = 300) -> WorkerResult | None:
    job = claim_next(conn, worker_id=worker_id, lease_seconds=lease_seconds)
    if not job:
        return None
    handler = handlers.get(job.job_type)
    if not handler:
        ok = complete(conn, job_id=job.id, worker_token=job.worker_token,
                      status="failed", error=f"no handler for {job.job_type}")
        return WorkerResult(job.id, "failed" if ok else "lost",
                            f"no handler for {job.job_type}")
    try:
        status, err = handler(conn, job)
    except Exception as exc:  # noqa: BLE001
        status, err = "retry_scheduled", f"{type(exc).__name__}: {exc}"[:1000]
    ok = complete(conn, job_id=job.id, worker_token=job.worker_token,
                  status=status, error=err)
    return WorkerResult(job.id, status if ok else "lost", err)
