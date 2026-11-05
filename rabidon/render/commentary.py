from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rabidon.utils.hashing import sha256_file, sha256_json
from rabidon.utils.timeutil import utc_now_iso


class RenderError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path | None = None) -> None:
    # No shell=True (security). Capture output for diagnostics.
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-20:])
        raise RenderError(f"command failed: {args[0]}\n{tail}")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def render_commentary_preview(*, scene_plan: dict, narration_wav: Path | None,
                              ass_path: Path | None, out_dir: Path,
                              width: int = 480, height: int = 854, fps: int = 30) -> dict:
    if not ffmpeg_available():
        raise RenderError("ffmpeg/ffprobe not available")
    if scene_plan.get("status") != "resolved":
        raise RenderError("renderer requires resolved scene plan (ADR-010)")
    scenes = scene_plan.get("scenes") or []
    if not scenes:
        raise RenderError("no scenes")
    total_ms = max(s["timeline_end_ms"] for s in scenes)
    total_s = max(0.2, total_ms / 1000.0)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=out_dir) as td:
        tmp = Path(td)
        preview_tmp = tmp / "preview.mp4"
        manifest_tmp = tmp / "manifest.json"

        vf_parts = [f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                    f"fps={fps}", "format=yuv420p"]
        if ass_path and ass_path.exists():
            # Escape for ffmpeg filter path.
            esc = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            vf_parts.insert(0, f"subtitles='{esc}'")
        vf = ",".join(vf_parts)

        args = ["ffmpeg", "-y", "-f", "lavfi", "-i",
                f"color=c=0x111827:s={width}x{height}:r={fps}:d={total_s:.3f}"]
        if narration_wav and narration_wav.exists():
            args += ["-i", str(narration_wav), "-map", "0:v:0", "-map", "1:a:0",
                     "-c:a", "aac", "-shortest"]
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                     "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-shortest"]
        args += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", str(preview_tmp)]
        _run(args)

        # Validate with ffprobe before promoting.
        probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(preview_tmp)]
        proc = subprocess.run(probe, capture_output=True, text=True)
        if proc.returncode != 0 or not proc.stdout.strip():
            raise RenderError("ffprobe validation failed")

        artifact_hash = sha256_file(preview_tmp)
        manifest = {
            "schema_version": 1,
            "kind": "preview",
            "template": {"id": "commentary_v1", "version": "0.1.0"},
            "scene_plan_hash": sha256_json(scene_plan),
            "timing_revision_id": scene_plan.get("timing_revision_id"),
            "settings": {"width": width, "height": height, "fps": fps},
            "tool_versions_runtime": {},
            "artifact_hash": artifact_hash,
            "created_at": utc_now_iso(),
            "reproducibility_note": "Traceable rerun from recorded inputs/versions; byte-identical output across machines/FFmpeg versions is not guaranteed (ADR-011).",
        }
        manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                                encoding="utf-8")
        manifest["manifest_hash"] = sha256_file(manifest_tmp)
        manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                                encoding="utf-8")

        # Atomic promote (same filesystem).
        preview_path = out_dir / "preview.mp4"
        manifest_path = out_dir / "manifest.json"
        os.replace(preview_tmp, preview_path)
        os.replace(manifest_tmp, manifest_path)
    return {"preview_path": str(preview_path), "manifest_path": str(manifest_path),
            "manifest": manifest}
