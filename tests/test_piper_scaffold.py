from pathlib import Path

import pytest

from rabidon.tts.base import VoiceConfig
from rabidon.tts.piper import PiperNotReady, PiperProvider, voice_readiness


def test_piper_requires_adr009_config_before_use(tmp_path: Path):
    p = PiperProvider(VoiceConfig(provider="recorded"))
    with pytest.raises(PiperNotReady):
        p.validate_ready()
    p2 = PiperProvider(VoiceConfig(provider="piper", voice_id="hi", model_path=tmp_path / "m.onnx"))
    with pytest.raises(PiperNotReady):  # licence_ref/binary/model missing
        p2.validate_ready()


def test_voice_readiness_reports_unresolved_and_missing_assets(tmp_path: Path):
    r = voice_readiness(VoiceConfig(provider="recorded"))
    assert r["provider"] == "recorded"
    r2 = voice_readiness(VoiceConfig(provider="piper", voice_id="hi", model_path=tmp_path / "m.onnx"))
    assert r2["ready"] is False
    assert any("licence_ref" in x for x in r2["reasons"])
    assert any("model_path" in x or "not found" in x for x in r2["reasons"])


def test_voice_config_unresolved_guard():
    assert VoiceConfig(provider="unresolved").is_unresolved() is True
    assert VoiceConfig(provider="recorded").is_unresolved() is False
    assert VoiceConfig(provider="piper", voice_id="hi", model_path=Path("m.onnx")).is_unresolved() is True
