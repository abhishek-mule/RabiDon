from pathlib import Path

from rabidon.assets.rights import add_permission, check_assets_for_use, register_asset
from rabidon.db import connect, immediate_tx, migrate


def _db(tmp_path: Path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_unknown_or_pending_rights_block_external_preview(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            aid = register_asset(c, asset_type="graphic", local_path="x.png",
                                 content_hash="sha256:abc", owner="u", provenance="owned")
            add_permission(c, asset_id=aid, rights_basis="unknown",
                           rights_status="pending", permitted_uses=["local_preview"])
            d = check_assets_for_use(c, [aid], "external_preview")
        assert d.ok is False
        assert any("basis=unknown" in b or "status=pending" in b for b in d.blockers)
    finally:
        c.close()


def test_expired_rights_block_even_if_approved(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            aid = register_asset(c, asset_type="audio", local_path="a.wav",
                                 content_hash="sha256:def")
            add_permission(c, asset_id=aid, rights_basis="licensed",
                           rights_status="approved",
                           permitted_uses=["external_preview", "private_upload"],
                           expires_at="2020-01-01T00:00:00+00:00")
            d = check_assets_for_use(c, [aid], "external_preview",
                                     now_iso="2026-01-01T00:00:00+00:00")
        assert d.ok is False
        assert any("expired" in b for b in d.blockers)
    finally:
        c.close()


def test_approved_rights_allow_permitted_use_only(tmp_path: Path):
    c = _db(tmp_path)
    try:
        with immediate_tx(c):
            aid = register_asset(c, asset_type="graphic", local_path="x.png",
                                 content_hash="sha256:ghi")
            add_permission(c, asset_id=aid, rights_basis="owned",
                           rights_status="approved",
                           permitted_uses=["local_preview", "final_render"])
            ok = check_assets_for_use(c, [aid], "local_preview")
            bad = check_assets_for_use(c, [aid], "public_release")
        assert ok.ok is True
        assert bad.ok is False
    finally:
        c.close()
