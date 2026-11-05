from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from rabidon.tts.base import VoiceConfig
from rabidon.tts.normalize import load_pronunciation_dict, normalize_for_tts
from rabidon.tts.segments import Segment, wav_duration_ms, wav_is_silent


class PiperNotReady(RuntimeError):
    pass


def voice_readiness(config: VoiceConfig) -> dict:
    """Non-mutating readiness report for ADR-009 operator checklist/harness."""
    reasons: list[str] = []
    if config.provider in ("recorded", "unresolved", ""):
        return {"ready": config.provider == "recorded", "provider": config.provider or "unresolved",
                "reasons": ["ADR-009: Piper voice not locked; recorded/unresolved fallback active"]}
    if config.provider != "piper":
        reasons.append("provider must be piper or recorded")
    if not config.voice_id:
        reasons.append("voice_id missing")
    if not config.model_path:
        reasons.append("model_path missing")
    elif not Path(config.model_path).exists():
        reasons.append("model_path not found (no auto-download)")
    if not config.licence_ref:
        reasons.append("licence_ref missing")
    piper = str(config.piper_bin) if config.piper_bin else shutil.which("piper")
    if not piper or not Path(piper).exists():
        reasons.append("piper binary not found")
    if config.pronunciation_dict and not Path(config.pronunciation_dict).exists():
        reasons.append("pronunciation_dict path missing")
    return {"ready": not reasons, "provider": config.provider, "piper_bin": piper, "reasons": reasons}


class PiperProvider:
    """ADR-009 scaffold: synthesis only when operator-supplied binary+model+licence are present.
    Never guesses/downloads a voice/model. Recorded fallback remains valid."""

    def __init__(self, config: VoiceConfig):
        self.config = config

    def validate_ready(self) -> None:
        r = voice_readiness(self.config)
        if self.config.provider != "piper":
            raise PiperNotReady("provider is not piper")
        if not r["ready"]:
            raise PiperNotReady("ADR-009: " + "; ".join(r["reasons"]))

    def synthesize(self, texts: list[str], out_dir: Path) -> list[Segment]:
        self.validate_ready()
        rules = load_pronunciation_dict(self.config.pronunciation_dict)
        out_dir.mkdir(parents=True, exist_ok=True)
        piper = str(self.config.piper_bin) if self.config.piper_bin else (shutil.which("piper") or "piper")
        segments: list[Segment] = []
        cursor = 0
        for i, raw_text in enumerate(texts):
            text = normalize_for_tts(raw_text, None)
            for src, repl in rules:
                if src:
                    text = text.replace(src, repl)
            path = out_dir / f"seg_{i:03d}.wav"
            # Arg array, no shell. No model download; operator supplies local model.
            proc = subprocess.run(
                [piper, "--model", str(self.config.model_path), "--output_file", str(path)],
                input=text, text=True, capture_output=True,
            )
            if proc.returncode != 0 or not path.exists():
                segments.append(Segment(i, text, str(path), cursor, cursor, 0, "failed",
                                        (proc.stderr or proc.stdout)[-300:]))
                continue
            dur = wav_duration_ms(path)
            status = "ok"
            err = None
            if dur <= 0 or wav_is_silent(path):
                status = "silent" if dur > 0 else "failed"
                err = "silent/empty output"
            end = cursor + dur
            segments.append(Segment(i, text, str(path), cursor, end, dur, status, err))
            cursor = end
        return segments
