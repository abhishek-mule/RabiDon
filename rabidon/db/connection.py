from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from rabidon.db.migrations import migrate as run_migrations


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # Pragmas: WAL on local disk, FK integrity, bounded busy handling.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def immediate_tx(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    # Short transaction for state transitions/job claims only.
    # NEVER hold this open during rendering or network calls.
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def migrate(conn: sqlite3.Connection) -> list[int]:
    return run_migrations(conn)
