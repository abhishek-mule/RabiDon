from __future__ import annotations

import json
import math
import wave
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Segment:
    index: int
    text: str
    audio_path: str | None
    start_ms: int
    end_ms: int
    duration_ms: int
    status: str  # ok|failed|silent
    error: str | None = None


def wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
    if rate <= 0:
        return 0
    return int(round((frames / rate) * 1000))


def wav_is_silent(path: Path, threshold: int = 64) -> bool:
    # Simple peak check for fixture/recorded WAV (16-bit PCM). Not a loudness standard.
    try:
        with wave.open(str(path), "rb") as wf:
            if wf.getsampwidth() != 2:
                return False
            frames = wf.readframes(wf.getnframes())
    except wave.Error:
        return True
    if not frames:
        return True
    peak = 0
    # sample a subset for speed
    step = max(2, (len(frames) // 20000) * 2)
    for i in range(0, len(frames) - 1, step):
        val = int.from_bytes(frames[i:i + 2], "little", signed=True)
        a = abs(val)
        if a > peak:
            peak = a
            if peak > threshold:
                return False
    return peak <= threshold


def write_silence_wav(path: Path, duration_ms: int, rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nframes = max(1, int(rate * duration_ms / 1000))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * nframes)


def segments_to_json(segments: list[Segment]) -> str:
    return json.dumps([asdict(s) for s in segments], ensure_ascii=False, sort_keys=True)
