import wave
from pathlib import Path

import pytest

from rabidon.render.commentary import ffmpeg_available, render_commentary_preview
from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
from rabidon.tts.recorded import import_recorded_segments


def _tone_wav(path: Path, duration_ms: int = 700, rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(rate * duration_ms / 1000)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            val = 12000 if (i // 40) % 2 == 0 else -12000
            frames += int(val).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(frames))


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_ffmpeg_preview_renders_and_writes_manifest(tmp_path: Path):
    a = tmp_path / "a.wav"
    _tone_wav(a, 900)
    prov = build_provisional(1, ["परीक्षण"])
    segs = import_recorded_segments(["परीक्षण"], [a])
    resolved = resolve_with_segments(prov, segs, "tim1")
    out = tmp_path / "out"
    res = render_commentary_preview(scene_plan=resolved.plan, narration_wav=a,
                                    ass_path=None, out_dir=out)
    assert Path(res["preview_path"]).exists()
    assert Path(res["manifest_path"]).exists()
    m = res["manifest"]
    assert m["scene_plan_hash"].startswith("sha256:")
    assert "byte-identical output" in m["reproducibility_note"].lower() or "traceable" in m["reproducibility_note"].lower()
