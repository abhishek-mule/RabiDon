from __future__ import annotations

import sqlite3

from rabidon.assets.rights import add_permission, register_asset


def cli_register_asset(conn: sqlite3.Connection, *, asset_type: str, local_path: str,
                       content_hash: str, owner: str | None = None,
                       provenance: str | None = None) -> int:
    return register_asset(conn, asset_type=asset_type, local_path=local_path,
                          content_hash=content_hash, owner=owner, provenance=provenance)


def cli_add_permission(conn: sqlite3.Connection, **kwargs) -> int:
    return add_permission(conn, **kwargs)
