import wave
from pathlib import Path

from rabidon.db import connect, immediate_tx, migrate
from rabidon.db.repositories import editorial, media
from rabidon.jobs.handlers import default_handlers, handle_awaiting_manual, handle_publish_requires_approval
from rabidon.jobs.queue import ClaimedJob


def _silence(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * 22050)


def test_awaiting_manual_and_approval_handlers():
    h = default_handlers()
    for name in ("awaiting_manual_input", "publish_external_requires_approval"):
        assert name in h
    job = ClaimedJob(1, "awaiting_manual_input", {"reason": "ADR-009"}, "t", 1)
    assert handle_awaiting_manual(None, job)[0] == "awaiting_manual_input"  # type: ignore[arg-type]
    job2 = ClaimedJob(2, "publish_external_requires_approval", {}, "t", 1)
    st, msg = handle_publish_requires_approval(None, job2)  # type: ignore[arg-type]
    assert st == "awaiting_approval"
    assert "no upload performed" in (msg or "").lower()


def test_default_handlers_have_no_external_transport():
    keys = " ".join(default_handlers().keys())
    assert "telegram_send" not in keys
    assert "youtube_upload" not in keys
    assert "http" not in keys
