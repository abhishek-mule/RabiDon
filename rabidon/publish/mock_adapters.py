from __future__ import annotations

from dataclasses import dataclass, field

from rabidon.publish.ports import LiveExternalActionDisabled, ProbeObservation


@dataclass
class InMemorySessionRefStore:
    """Test-only opaque store. Keeps values in-memory; production must use secure storage."""
    _data: dict[str, str] = field(default_factory=dict)
    _seq: int = 0

    def put(self, attempt_id: int, secret_value: str) -> str:
        self._seq += 1
        ref = f"sessionref:opaque:{attempt_id}:{self._seq}"
        self._data[ref] = secret_value
        return ref

    def get(self, ref: str) -> str | None:
        return self._data.get(ref)


@dataclass
class MockPublisherAdapter:
    """Offline mock. No network."""
    observations: dict[tuple[str, str, str | None], ProbeObservation] = field(default_factory=dict)
    prepared: list[dict] = field(default_factory=list)

    def prepare_session(self, *, package_hash: str, destination: str, action: str) -> str:
        self.prepared.append({"package_hash": package_hash, "destination": destination, "action": action})
        return f"mock-session:{destination}:{action}"

    def probe_status(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> ProbeObservation:
        return self.observations.get(
            (destination, idempotency_key, remote_id),
            ProbeObservation(state="unknown", remote_id=remote_id, detail="mock: no observation"),
        )

    def lookup(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> dict:
        # Compatibility with existing PublisherProbe protocol.
        o = self.probe_status(destination=destination, idempotency_key=idempotency_key, remote_id=remote_id)
        return {
            "state": o.state, "remote_id": o.remote_id, "remote_url": o.remote_url,
            "processing_state": o.processing_state, "visibility_state": o.visibility_state,
            "detail": o.detail,
        }


class YouTubePublisherAdapterLiveDisabled:
    def prepare_session(self, *, package_hash: str, destination: str, action: str) -> str:
        raise LiveExternalActionDisabled("live YouTube actions are disabled in this build/plan")

    def probe_status(self, *, destination: str, idempotency_key: str, remote_id: str | None) -> ProbeObservation:
        raise LiveExternalActionDisabled("live YouTube probe is disabled in this build/plan")


class TelegramTransportLiveDisabled:
    def send_preview(self, *, chat_id: str, text: str, artifact_path: str | None) -> str:
        raise LiveExternalActionDisabled("live Telegram sends are disabled in this build/plan")
