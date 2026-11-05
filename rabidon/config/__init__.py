from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    env: str = "development"
    db_path: Path = Path("./data/rabidon.db")
    data_dir: Path = Path("./data")
    output_dir: Path = Path("./output")
    log_level: str = "INFO"
    # ADR-009: voice unresolved until selection+licence spike. Default remains recorded.
    tts_provider: str = "recorded"
    voice_id: str | None = None
    piper_bin: str | None = None
    voice_model_path: str | None = None
    voice_licence_ref: str | None = None
    pronunciation_dict: str | None = None


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def load_settings() -> Settings:
    voice_id = os.getenv("RABIDON_VOICE_ID") or None
    return Settings(
        env=_env("RABIDON_ENV", "development"),
        db_path=Path(_env("RABIDON_DB_PATH", "./data/rabidon.db")),
        data_dir=Path(_env("RABIDON_DATA_DIR", "./data")),
        output_dir=Path(_env("RABIDON_OUTPUT_DIR", "./output")),
        log_level=_env("RABIDON_LOG_LEVEL", "INFO"),
        tts_provider=_env("RABIDON_TTS_PROVIDER", "recorded"),
        voice_id=voice_id,
        piper_bin=os.getenv("RABIDON_PIPER_BIN") or None,
        voice_model_path=os.getenv("RABIDON_VOICE_MODEL_PATH") or None,
        voice_licence_ref=os.getenv("RABIDON_VOICE_LICENCE_REF") or None,
        pronunciation_dict=os.getenv("RABIDON_PRONUNCIATION_DICT") or None,
    )
