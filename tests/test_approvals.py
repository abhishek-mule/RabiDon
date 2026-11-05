from pathlib import Path

from rabidon.approvals.service import create_request, decide
from rabidon.db import connect, immediate_tx, migrate


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_approval_hash_mismatch_and_duplicate_callback_safe(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            req = create_request(c, action="telegram_preview", object_type="render_run",
                                 object_id="1", object_version="v1",
                                 object_hash="sha256:aaa")
            # Hash mismatch invalidates.
            out = decide(c, token=req.token, approver="tg:1", decision="approved",
                         current_object_hash="sha256:bbb")
        assert out.ok is False and out.status == "hash_mismatch"

        with immediate_tx(c):
            req2 = create_request(c, action="telegram_preview", object_type="render_run",
                                  object_id="1", object_version="v1",
                                  object_hash="sha256:ccc")
            ok = decide(c, token=req2.token, approver="tg:1", decision="approved",
                        current_object_hash="sha256:ccc")
            dup = decide(c, token=req2.token, approver="tg:1", decision="approved",
                         current_object_hash="sha256:ccc")
        assert ok.ok is True
        assert dup.ok is False  # harmless: not pending
    finally:
        c.close()


def test_private_upload_not_public_release(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            req = create_request(c, action="private_upload", object_type="publish_package",
                                 object_id="pkg1", object_version="v1",
                                 object_hash="sha256:pkg")
        row = c.execute("SELECT action FROM approval_requests WHERE id=?",
                        (req.request_id,)).fetchone()
        assert row["action"] == "private_upload"
        # Separate action type required for public release (enforced by caller/policy; stored distinctly).
        assert row["action"] != "public_release"
    finally:
        c.close()
