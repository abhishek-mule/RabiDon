from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

from rabidon.qa.report import Check, QaReport

PROBE_TIMEOUT_S = 30


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _ffprobe() -> str | None:
    return shutil.which("ffprobe")


def _ffprobe_json(path: Path) -> dict | None:
    exe = _ffprobe()
    if not exe:
        return None
    args = [exe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=PROBE_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def _run_ffmpeg_null(path: Path, af: str) -> tuple[int, str, str]:
    exe = _ffmpeg()
    if not exe:
        return 127, "", "ffmpeg not found"
    args = [exe, "-hide_banner", "-nostats", "-i", str(path), "-af", af, "-f", "null", "-"]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=PROBE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as e:
        return 126, "", str(e)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _probe_af(name: str, path: Path, af: str, parser) -> Check:
    code, out, err = _run_ffmpeg_null(path, af)
    text = out + "\n" + err
    if code == 127:
        return Check(name, "not_run", "ffmpeg unavailable")
    if "No such filter" in text or "Unknown filter" in text:
        return Check(name, "not_run", "filter unavailable in this ffmpeg build")
    if code == 124:
        return Check(name, "not_run", "probe timeout")
    if code != 0 and not text.strip():
        return Check(name, "not_run", f"probe failed (exit {code})")
    try:
        return parser(text)
    except Exception as e:  # noqa: BLE001
        return Check(name, "manual_required", f"probe output not parsed: {e}")


def _parse_silence(text: str) -> Check:
    silences = [l for l in text.splitlines() if "silence_start" in l or "silence_end" in l or "silence_duration" in l]
    if not silences:
        return Check("silence", "pass", "no silence intervals reported")
    joined = "; ".join(silences[:4])
    return Check("silence", "warn", joined, data={"interval_markers": len(silences)})


def _parse_volume(text: str) -> Check:
    mean = maxv = None
    for line in text.splitlines():
        if "mean_volume:" in line:
            try:
                mean = float(line.split("mean_volume:")[1].split("dB")[0].strip())
            except ValueError:
                pass
        if "max_volume:" in line:
            try:
                maxv = float(line.split("max_volume:")[1].split("dB")[0].strip())
            except ValueError:
                pass
    if mean is None and maxv is None:
        raise ValueError("no volume fields")
    # Conservative thresholds for short narration; very hot peaks warn.
    result = "pass"
    detail = f"mean={mean}dB max={maxv}dB"
    if maxv is not None and maxv >= -0.1:
        result = "warn"
        detail += " (possible clipping/near-full-scale)"
    if mean is not None and mean > -8:
        result = "warn"
        detail += " (unusually loud mean)"
    return Check("loudness_volume", result, detail, data={"mean_db": mean, "max_db": maxv})


def _probe_black_frames(path: Path) -> Check:
    exe = _ffmpeg()
    if not exe:
        return Check("black_frames", "not_run", "ffmpeg unavailable")
    args = [exe, "-hide_banner", "-nostats", "-i", str(path),
            "-vf", "blackdetect=d=0.5:pix_th=0.10", "-an", "-f", "null", "-"]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=PROBE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return Check("black_frames", "not_run", "probe timeout")
    except OSError as e:
        return Check("black_frames", "not_run", str(e))
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if "No such filter" in text or "Unknown filter" in text:
        return Check("black_frames", "not_run", "blackdetect unavailable")
    blacks = [l for l in text.splitlines() if "black_start" in l]
    if not blacks:
        return Check("black_frames", "pass", "no black intervals >= 0.5s detected")
    return Check("black_frames", "warn", blacks[0][:240], data={"intervals": len(blacks)})


def qa_media_file(path: Path, *, expected_kind: str = "video") -> QaReport:
    qa = QaReport()
    if not path.exists():
        qa.add(Check("file_exists", "fail", str(path)))
        return qa
    qa.add(Check("file_exists", "pass"))
    info = _ffprobe_json(path)
    if info is None:
        qa.add(Check("ffprobe", "manual_required" if _ffprobe() else "not_run",
                     "ffprobe unavailable or failed"))
        qa.add(Check("silence", "not_run" if not _ffmpeg() else "manual_required", "no probe metadata"))
        qa.add(Check("loudness_volume", "not_run" if not _ffmpeg() else "manual_required", "no probe metadata"))
        qa.add(Check("black_frames", "not_run" if not _ffmpeg() else "manual_required", "no probe metadata"))
        qa.add(Check("hindi_glyph_review", "manual_required", "human must verify Devanagari rendering"))
        return qa
    streams = info.get("streams") or []
    if expected_kind == "video":
        if not any(s.get("codec_type") == "video" for s in streams):
            qa.add(Check("video_stream", "fail", "no video stream"))
        else:
            qa.add(Check("video_stream", "pass"))
        if not any(s.get("codec_type") == "audio" for s in streams):
            qa.add(Check("audio_stream", "fail", "no audio stream"))
        else:
            qa.add(Check("audio_stream", "pass"))
    dur = None
    try:
        dur = float((info.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        dur = None
    if dur is None or dur <= 0:
        qa.add(Check("duration", "fail", "missing/zero duration"))
    else:
        qa.add(Check("duration", "pass", data={"seconds": round(dur, 3)}))

    qa.add(_probe_af("silence", path, "silencedetect=noise=-35dB:d=0.4", _parse_silence))
    qa.add(_probe_af("loudness_volume", path, "volumedetect", _parse_volume))
    qa.add(_probe_black_frames(path) if expected_kind == "video" else Check("black_frames", "not_run", "audio-only"))
    qa.add(Check("hindi_glyph_review", "manual_required", "human must verify Devanagari rendering"))
    return qa
