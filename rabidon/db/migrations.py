from __future__ import annotations

import sqlite3
from importlib import resources
from pathlib import Path

MIGRATIONS_PACKAGE = "rabidon.db.sql"


def _migration_files() -> list[tuple[int, str]]:
    # sql files are read from filesystem path alongside package for simplicity.
    sql_dir = Path(__file__).with_name("sql")
    items: list[tuple[int, str]] = []
    for p in sorted(sql_dir.glob("*.sql")):
        ver = int(p.stem.split("_", 1)[0])
        items.append((ver, p.read_text(encoding="utf-8")))
    return items


def latest_version() -> int:
    files = _migration_files()
    return files[-1][0] if files else 0


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    try:
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    except sqlite3.OperationalError:
        return set()
    return {int(r[0]) for r in rows}


def migrate(conn: sqlite3.Connection) -> list[int]:
    applied = applied_versions(conn)
    newly: list[int] = []
    for ver, sql in _migration_files():
        if ver in applied:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))",
            (ver,),
        )
        conn.commit()
        newly.append(ver)
    return newly
