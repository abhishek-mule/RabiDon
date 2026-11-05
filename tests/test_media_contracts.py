import wave
from pathlib import Path

from rabidon.captions.builder import validate_segments, write_srt
from rabidon.publish.package import build_package
from rabidon.scene_planner.planner import build_provisional, resolve_with_segments
from rabidon.tts.recorded import import_recorded_segments
from rabidon.tts.segments import write_silence_wav


def _tone_wav(path: Path, duration_ms: int = 800, rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(rate * duration_ms / 1000)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        # simple audible non-zero PCM
        frames = bytearray()
        for i in range(n):
            val = 12000 if (i // 40) % 2 == 0 else -12000
            frames += int(val).to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(frames))


def test_provisional_then_resolved_timing(tmp_path: Path):
    prov = build_provisional(1, ["पहला वाक्य", "दूसरा वाक्य"])
    assert prov.status == "provisional"
    assert prov.plan["scenes"][0]["timeline_start_ms"] is None
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    _tone_wav(a, 500)
    _tone_wav(b, 700)
    segs = import_recorded_segments(["पहला वाक्य", "दूसरा वाक्य"], [a, b])
    resolved = resolve_with_segments(prov, segs, timing_revision_id="tim1")
    assert resolved.status == "resolved"
    assert resolved.plan["scenes"][0]["timeline_start_ms"] == 0
    assert resolved.plan["scenes"][1]["timeline_start_ms"] == segs[0].end_ms
    assert resolved.plan_hash.startswith("sha256:")


def test_silent_segment_fails_caption_validation(tmp_path: Path):
    p = tmp_path / "s.wav"
    write_silence_wav(p, 500)
    segs = import_recorded_segments(["x"], [p])
    issues = validate_segments(segs)
    assert any(i.code == "segment_status" and "silent" in i.detail for i in issues)


def test_publish_package_has_no_approval_refs():
    pkg, h = build_package(video_id=1, render_run_id=1, artifact_hash="sha256:a",
                           manifest_hash="sha256:b", destination="youtube",
                           action="private_upload", privacy="private", title="t")
    assert "approval_refs" not in pkg
    assert "approval_decisions" not in str(pkg)
    assert h.startswith("sha256:")


def test_caption_writer_outputs_utf8_srt(tmp_path: Path):
    a = tmp_path / "a.wav"
    _tone_wav(a, 500)
    segs = import_recorded_segments(["नमस्ते दुनिया"], [a])
    out = tmp_path / "c.srt"
    write_srt(segs, out)
    text = out.read_text(encoding="utf-8")
    assert "नमस्ते" in text
    assert "-->" in text
