"""Track B contracts (mock/offline only). Live adapters are disabled by default."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LiveExternalActionDisabled(RuntimeError):
    """Raised by LiveDisabled adapters. No network, no credentials."""


@dataclass(frozen=True)
class ProbeObservation:
    state: str  # uploaded|not_found|unknown
    remote_id: str | None = None
    remote_url: str | None = None
    processing_state: str = "unknown"
    visibility_state: str = "unknown"
    detail: str | None = None


class PublisherProbePort(Protocol):
    def lookup(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> dict:
        ...


class SessionRefStore(Protocol):
    """Opaque session reference storage contract.
    Secret/session URI material must never be logged or placed in packages."""

    def put(self, attempt_id: int, secret_value: str) -> str:
        """Store secret_value out-of-band and return opaque ref."""

    def get(self, ref: str) -> str | None:
        ...


class PublisherAdapter(Protocol):
    def prepare_session(self, *, package_hash: str, destination: str, action: str) -> str:
        """Return opaque session ref (not a raw secret for logs/packages)."""

    def probe_status(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> ProbeObservation:
        ...


class PreviewTransportPort(Protocol):
    def send_preview(self, *, chat_id: str, text: str, artifact_path: str | None) -> str:
        ...
