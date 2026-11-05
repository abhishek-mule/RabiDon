import wave
from pathlib import Path

import pytest

from rabidon.qa.media import qa_media_file
from rabidon.render.commentary import ffmpeg_available


def _tone(path: Path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
        b = bytearray()
        for i in range(22050 // 2):
            v = 10000 if (i // 40) % 2 == 0 else -10000
            b += int(v).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(b))


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_ffprobe_qa_reports_probe_gaps_explicitly(tmp_path: Path):
    from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
    from rabidon.render.commentary import render_commentary_preview
    from rabidon.tts.recorded import import_recorded_segments
    a = tmp_path / "a.wav"; _tone(a)
    prov = build_provisional(1, ["x"])
    segs = import_recorded_segments(["x"], [a])
    plan = resolve_with_segments(prov, segs, "t").plan
    res = render_commentary_preview(scene_plan=plan, narration_wav=a, ass_path=None,
                                    out_dir=tmp_path / "o")
    qa = qa_media_file(Path(res["preview_path"]), expected_kind="video")
    names = {c.name: c.result for c in qa.checks}
    assert names.get("video_stream") == "pass"
    assert names.get("audio_stream") == "pass"
    # Probe-and-fallback: measured where possible, else not_run/manual_required; never pass-by-default.
    assert names.get("loudness_volume") in ("pass", "warn", "not_run", "manual_required")
    assert names.get("silence") in ("pass", "warn", "not_run", "manual_required")
    assert names.get("black_frames") in ("pass", "warn", "not_run", "manual_required")
    assert names.get("hindi_glyph_review") == "manual_required"
    assert qa.result in ("pass", "pass_with_warnings")
