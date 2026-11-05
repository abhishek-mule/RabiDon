from pathlib import Path

from rabidon.config import load_settings
from rabidon.db import connect, immediate_tx, migrate
from rabidon.utils.hashing import canonical_json, sha256_json
from rabidon.utils.money import paise_to_rupees_str, rupees_to_paise
from rabidon.utils.timeutil import utc_now_iso


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("RABIDON_TTS_PROVIDER", raising=False)
    monkeypatch.delenv("RABIDON_VOICE_ID", raising=False)
    s = load_settings()
    # ADR-009: unresolved/recorded until voice spike; never assume a locked voice.
    assert s.tts_provider in ("recorded", "unresolved")
    assert s.voice_id is None


def test_sqlite_pragmas_and_migrate(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        row = c.execute("PRAGMA journal_mode").fetchone()
        assert str(row[0]).lower() == "wal"
        fk = c.execute("PRAGMA foreign_keys").fetchone()
        assert int(fk[0]) == 1
        applied = migrate(c)
        assert 1 in applied and 2 in applied
        # idempotent
        assert migrate(c) == []
    finally:
        c.close()


def test_immediate_tx_commit_and_rollback(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    try:
        migrate(c)
        with immediate_tx(c):
            c.execute(
                "INSERT INTO audit_events(actor,action,object_type,created_at) VALUES ('t','a','x',strftime('%Y-%m-%dT%H:%M:%SZ','now'))"
            )
        n = c.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        assert n == 1
        try:
            with immediate_tx(c):
                c.execute(
                    "INSERT INTO audit_events(actor,action,object_type,created_at) VALUES ('t','b','x',strftime('%Y-%m-%dT%H:%M:%SZ','now'))"
                )
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        n2 = c.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        assert n2 == 1
    finally:
        c.close()


def test_hashing_money_time():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert sha256_json({"a": 1}).startswith("sha256:")
    assert rupees_to_paise("199.995") == 20000
    assert paise_to_rupees_str(12345) == "123.45"
    ts = utc_now_iso()
    assert ts.endswith("+00:00") or ts.endswith("Z")
