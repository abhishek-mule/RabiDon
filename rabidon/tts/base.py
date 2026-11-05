from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rabidon.tts.segments import Segment


@dataclass(frozen=True)
class VoiceProfile:
    """Operator-declared voice metadata for evidence/licence tracking (ADR-009)."""

    provider: str  # piper|recorded|unresolved
    voice_id: str | None = None
    model_id: str | None = None  # e.g. hi_IN-medium (candidate; not auto-selected)
    model_path: Path | None = None
    sample_rate: int | None = None
    speaker_id: int | None = None
    licence_ref: str | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class VoiceConfig:
    provider: str  # piper|recorded|unresolved
    voice_id: str | None = None
    model_path: Path | None = None
    licence_ref: str | None = None
    piper_bin: Path | None = None
    pronunciation_dict: Path | None = None
    profile: VoiceProfile | None = None

    def is_unresolved(self) -> bool:
        return self.provider in ("", "unresolved") or (
            self.provider == "piper" and not (self.voice_id and self.model_path and self.licence_ref)
        )


class TtsProvider(Protocol):
    def synthesize(self, texts: list[str], out_dir: Path) -> list[Segment]: ...
