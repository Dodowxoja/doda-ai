"""Ovoz registri testi — config nomiga qarab provayder qurish + mock + xatolar."""

from __future__ import annotations

import logging

import pytest

from code.doda.config import VoiceSettings
from code.doda.core.errors import ConfigError, SecretNotFoundError
from code.doda.providers.observability import BasicObservability
from code.doda.providers.voice import (
    EnergyVAD,
    FakeAudioInput,
    FakeAudioOutput,
    FakeSTT,
    FakeTTS,
    FakeVAD,
    build_audio_input,
    build_audio_output,
    build_stt,
    build_tts,
    build_vad,
)
from code.doda.providers.voice.audio import (
    LinuxRecorder,
    MacRecorder,
    WindowsRecorder,
)
from code.doda.providers.voice.stt import ElevenLabsSTT, WhisperSTT
from code.doda.providers.voice.tts import EdgeTTS, ElevenLabsTTS
from code.doda.providers.voice.vad import SileroVAD


class FakeSecrets:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._v = values or {}

    def get(self, key: str) -> str | None:
        return self._v.get(key)

    def require(self, key: str) -> str:
        value = self._v.get(key)
        if value is None:
            raise SecretNotFoundError(key)
        return value

    def set(self, key: str, value: str) -> None:
        self._v[key] = value


_SECRETS = FakeSecrets()


# ---------------- STT ----------------


def test_build_stt_whisper() -> None:
    assert isinstance(build_stt(VoiceSettings(stt_provider="whisper"), _SECRETS), WhisperSTT)


def test_build_stt_elevenlabs() -> None:
    stt = build_stt(VoiceSettings(stt_provider="elevenlabs", language="en"), _SECRETS)
    assert isinstance(stt, ElevenLabsSTT)


def test_build_stt_mock_and_mock_mode() -> None:
    assert isinstance(build_stt(VoiceSettings(stt_provider="mock"), _SECRETS), FakeSTT)
    assert isinstance(build_stt(VoiceSettings(mock_mode=True), _SECRETS), FakeSTT)


def test_build_stt_unknown_raises() -> None:
    with pytest.raises(ConfigError, match="STT provider"):
        build_stt(VoiceSettings(stt_provider="xyz"), _SECRETS)


def test_build_stt_elevenlabs_uz_warns(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("doda.test.reg")
    obs = BasicObservability(logger=logger)
    with caplog.at_level(logging.WARNING, logger="doda.test.reg"):
        build_stt(
            VoiceSettings(stt_provider="elevenlabs", language="uz"), _SECRETS, observability=obs
        )
    assert any("noaniq" in r.message for r in caplog.records)


# ---------------- TTS ----------------


def test_build_tts_edge_and_elevenlabs() -> None:
    assert isinstance(build_tts(VoiceSettings(tts_provider="edge_tts"), _SECRETS), EdgeTTS)
    assert isinstance(build_tts(VoiceSettings(tts_provider="elevenlabs"), _SECRETS), ElevenLabsTTS)


def test_build_tts_mock_and_unknown() -> None:
    assert isinstance(build_tts(VoiceSettings(mock_mode=True), _SECRETS), FakeTTS)
    assert isinstance(build_tts(VoiceSettings(tts_provider="mock"), _SECRETS), FakeTTS)
    with pytest.raises(ConfigError, match="TTS provider"):
        build_tts(VoiceSettings(tts_provider="xyz"), _SECRETS)


# ---------------- VAD ----------------


def test_build_vad_variants() -> None:
    assert isinstance(build_vad(VoiceSettings(vad_provider="energy")), EnergyVAD)
    assert isinstance(build_vad(VoiceSettings(vad_provider="silero")), SileroVAD)
    assert isinstance(build_vad(VoiceSettings(vad_provider="mock")), FakeVAD)
    assert isinstance(build_vad(VoiceSettings(mock_mode=True)), FakeVAD)
    with pytest.raises(ConfigError, match="VAD provider"):
        build_vad(VoiceSettings(vad_provider="xyz"))


# ---------------- Audio (OS detect) ----------------


def test_build_audio_explicit_os() -> None:
    assert isinstance(build_audio_input(VoiceSettings(audio_provider="macos")), MacRecorder)
    assert isinstance(build_audio_input(VoiceSettings(audio_provider="linux")), LinuxRecorder)
    assert isinstance(build_audio_input(VoiceSettings(audio_provider="windows")), WindowsRecorder)


def test_build_audio_mock_and_unknown() -> None:
    assert isinstance(build_audio_input(VoiceSettings(mock_mode=True)), FakeAudioInput)
    assert isinstance(build_audio_output(VoiceSettings(mock_mode=True)), FakeAudioOutput)
    assert isinstance(build_audio_input(VoiceSettings(audio_provider="mock")), FakeAudioInput)
    assert isinstance(build_audio_output(VoiceSettings(audio_provider="mock")), FakeAudioOutput)
    with pytest.raises(ConfigError, match="audio provider"):
        build_audio_input(VoiceSettings(audio_provider="xyz"))
    with pytest.raises(ConfigError, match="audio provider"):
        build_audio_output(VoiceSettings(audio_provider="xyz"))


@pytest.mark.parametrize(
    ("platform", "expected"),
    [("darwin", MacRecorder), ("linux", LinuxRecorder), ("win32", WindowsRecorder)],
)
def test_auto_detects_os(platform: str, expected: type, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("doda.providers.voice.registry.sys.platform", platform)
    assert isinstance(build_audio_input(VoiceSettings(audio_provider="auto")), expected)


def test_build_audio_output_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    from code.doda.providers.voice.audio import LinuxPlayer, MacPlayer, WindowsPlayer

    for platform, expected in (
        ("darwin", MacPlayer),
        ("linux", LinuxPlayer),
        ("win32", WindowsPlayer),
    ):
        monkeypatch.setattr("doda.providers.voice.registry.sys.platform", platform)
        assert isinstance(build_audio_output(VoiceSettings(audio_provider="auto")), expected)
