from pathlib import Path

from rabidon.tts.normalize import apply_pronunciation, load_pronunciation_dict, normalize_for_tts


def test_pronunciation_dict_applies(tmp_path: Path):
    p = tmp_path / "dict.tsv"
    p.write_text("Doraemon\tडोरेमोन\n# comment\nNobita\tनोबिता\n", encoding="utf-8")
    rules = load_pronunciation_dict(p)
    assert apply_pronunciation("Doraemon and Nobita", rules) == "डोरेमोन and नोबिता"


def test_pronunciation_dict_json_and_missing_file(tmp_path: Path):
    p = tmp_path / "dict.json"
    p.write_text('{"Doraemon":"डोरेमोन"}', encoding="utf-8")
    assert load_pronunciation_dict(p) == [("Doraemon", "डोरेमोन")]
    assert load_pronunciation_dict(tmp_path / "missing.json") == []
    assert normalize_for_tts("Doraemon", p) == "डोरेमोन"
