from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rabidon.assets.rights import check_assets_for_use
from rabidon.qa.media import qa_media_file
from rabidon.qa.report import Check, QaReport
from rabidon.render.commentary import RenderError, ffmpeg_available
from rabidon.utils.hashing import sha256_file, sha256_json
from rabidon.utils.timeutil import utc_now_iso


def _run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError((proc.stderr or proc.stdout)[-1200:])


def render_final_local(*, scene_plan: dict, narration_wav: Path | None, ass_path: Path | None,
                       asset_ids: list[int], rights_conn, out_dir: Path,
                       width: int = 1080, height: int = 1920, fps: int = 30) -> dict:
    # Local artifact creation only. No upload/send. Rights checked for final_render.
    if not ffmpeg_available():
        raise RenderError("ffmpeg/ffprobe not available")
    if scene_plan.get("status") != "resolved":
        raise RenderError("renderer requires resolved scene plan (ADR-010)")
    rights = check_assets_for_use(rights_conn, asset_ids, "final_render")
    qa = QaReport()
    qa.add(Check("rights_final_render", "pass" if rights.ok else "fail",
                 None if rights.ok else "; ".join(rights.blockers)))
    if not rights.ok:
        qa_path = out_dir / "qa_report.json"
        qa.save(qa_path)
        return {"ok": False, "qa": qa.to_dict(), "qa_path": str(qa_path)}

    scenes = scene_plan.get("scenes") or []
    total_s = max(0.2, max(s["timeline_end_ms"] for s in scenes) / 1000.0)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out_dir) as td:
        tmp = Path(td)
        final_tmp = tmp / "final.mp4"
        vf_parts = [f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2", f"fps={fps}", "format=yuv420p"]
        if ass_path and ass_path.exists():
            esc = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            vf_parts.insert(0, f"subtitles='{esc}'")
        args = ["ffmpeg", "-y", "-f", "lavfi", "-i",
                f"color=c=0x111827:s={width}x{height}:r={fps}:d={total_s:.3f}"]
        if narration_wav and narration_wav.exists():
            args += ["-i", str(narration_wav), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-shortest"]
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                     "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-shortest"]
        args += ["-vf", ",".join(vf_parts), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", str(final_tmp)]
        _run(args)
        subprocess.run(["ffprobe", "-v", "error", str(final_tmp)], check=True, capture_output=True)
        artifact_hash = sha256_file(final_tmp)
        manifest = {
            "schema_version": 1, "kind": "final",
            "template": {"id": "commentary_v1", "version": "0.1.0"},
            "scene_plan_hash": sha256_json(scene_plan),
            "settings": {"width": width, "height": height, "fps": fps},
            "asset_ids": asset_ids, "artifact_hash": artifact_hash,
            "created_at": utc_now_iso(),
            "reproducibility_note": "Traceable rerun from recorded inputs/versions; byte-identical output across machines/FFmpeg versions is not guaranteed (ADR-011).",
        }
        manifest_tmp = tmp / "manifest.json"
        manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                                encoding="utf-8")
        manifest["manifest_hash"] = sha256_file(manifest_tmp)
        manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                                encoding="utf-8")
        os.replace(final_tmp, out_dir / "final.mp4")
        os.replace(manifest_tmp, out_dir / "manifest.json")
    media_qa = qa_media_file(out_dir / "final.mp4")
    for c in media_qa.checks:
        qa.add(c)
    qa_path = out_dir / "qa_report.json"
    qa.save(qa_path)
    return {"ok": qa.result != "fail", "artifact": str(out_dir / "final.mp4"),
            "manifest": str(out_dir / "manifest.json"), "qa": qa.to_dict(), "qa_path": str(qa_path)}
