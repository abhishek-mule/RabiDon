from __future__ import annotations

from pathlib import Path

from rabidon.tts.segments import Segment, wav_duration_ms, wav_is_silent, write_silence_wav


def import_recorded_segments(texts: list[str], audio_paths: list[Path]) -> list[Segment]:
    if len(texts) != len(audio_paths):
        raise ValueError("texts and audio_paths length must match")
    segments: list[Segment] = []
    cursor = 0
    for i, (text, path) in enumerate(zip(texts, audio_paths)):
        if not path.exists():
            segments.append(Segment(i, text, str(path), cursor, cursor, 0, "failed", "missing file"))
            continue
        dur = wav_duration_ms(path)
        status = "silent" if wav_is_silent(path) else "ok"
        if dur <= 0:
            status = "failed"
        end = cursor + dur
        segments.append(Segment(i, text, str(path), cursor, end, dur, status,
                                "silent audio" if status == "silent" else None))
        cursor = end
    return segments


def synthesize_placeholder(texts: list[str], out_dir: Path, ms_per_char: int = 45) -> list[Segment]:
    # Recorded fallback for offline tests/dev: deterministic non-silent-ish timing using
    # short tone-like PCM is not added (keeps deps zero). We generate silent WAVs but mark
    # them as failed/silent so QA blocks — caller must supply real recorded audio for real use.
    segments: list[Segment] = []
    cursor = 0
    for i, text in enumerate(texts):
        dur = max(600, min(8000, len(text) * ms_per_char))
        path = out_dir / f"seg_{i:03d}.wav"
        write_silence_wav(path, dur)
        end = cursor + dur
        segments.append(Segment(i, text, str(path), cursor, end, dur, "silent",
                                "placeholder audio; supply recorded narration (ADR-009 fallback)"))
        cursor = end
    return segments
