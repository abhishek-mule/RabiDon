from pathlib import Path

from rabidon.qa import media as qam


def test_qa_missing_file_fails():
    qa = qam.qa_media_file(Path("/tmp/definitely-missing-rabidon-file.mp4"))
    assert qa.result == "fail"
    assert qa.checks[0].name == "file_exists"


def test_qa_no_ffprobe_marks_manual_or_not_run(monkeypatch, tmp_path):
    p = tmp_path / "x.mp4"; p.write_bytes(b"x")
    monkeypatch.setattr(qam, "_ffprobe_json", lambda path: None)
    monkeypatch.setattr(qam, "_ffprobe", lambda: None)
    monkeypatch.setattr(qam, "_ffmpeg", lambda: None)
    qa = qam.qa_media_file(p)
    names = {c.name: c.result for c in qa.checks}
    assert names["ffprobe"] == "not_run"
    assert names["hindi_glyph_review"] == "manual_required"
    assert "pass" not in (names["ffprobe"],)  # explicit
