"""Ovoz provayder registri — config nomiga qarab STT/TTS/VAD/audio quradi.

Provider-specific kod core'ga kirmaydi; bu yagona joy config (``VoiceSettings``) + sirlar
(``SecretStore``) asosida konkret adapterni tanlaydi. Yangi provider qo'shish = shu yerga bitta
tarmoq, core o'zgarmaydi. ``mock_mode`` yoqilsa — barchasi soxta (kalitsiz test/ishlash).
"""

from __future__ import annotations

import sys

from doda.config import VoiceSettings
from doda.core.errors import ConfigError
from doda.core.interfaces.observability import Observability
from doda.core.interfaces.secrets import SecretStore
from doda.core.interfaces.voice import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
    VoiceActivityDetector,
)
from doda.providers.voice.audio import (
    FakeAudioInput,
    FakeAudioOutput,
    LinuxPlayer,
    LinuxRecorder,
    MacPlayer,
    MacRecorder,
    WindowsPlayer,
    WindowsRecorder,
)
from doda.providers.voice.stt import ElevenLabsSTT, FakeSTT, WhisperSTT
from doda.providers.voice.stt.elevenlabs import UNCERTAIN_LANGUAGES
from doda.providers.voice.tts import EdgeTTS, ElevenLabsTTS, FakeTTS
from doda.providers.voice.vad import EnergyVAD, FakeVAD, SileroVAD

_STT_KEY = "speech.stt.key"
_TTS_KEY = "speech.tts.key"


def _detect_os() -> str:
    """Joriy OS nomini qaytaradi (macos/linux/windows)."""
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


def build_stt(
    settings: VoiceSettings,
    secrets: SecretStore,
    *,
    observability: Observability | None = None,
) -> SpeechToText:
    """Config nomiga qarab STT provayderini quradi."""
    if settings.mock_mode:
        return FakeSTT()
    provider = settings.stt_provider.lower()
    if provider == "whisper":
        return WhisperSTT()
    if provider == "elevenlabs":
        if observability is not None and settings.language in UNCERTAIN_LANGUAGES:
            observability.log(
                "warning",
                "ElevenLabs STT o'zbek tili sifati noaniq — fallback tavsiya etiladi",
                language=settings.language,
            )
        return ElevenLabsSTT(secrets.get(_STT_KEY) or "")
    if provider == "mock":
        return FakeSTT()
    raise ConfigError(f"Noma'lum STT provider: '{settings.stt_provider}'")


def build_tts(
    settings: VoiceSettings,
    secrets: SecretStore,
    *,
    observability: Observability | None = None,
) -> TextToSpeech:
    """Config nomiga qarab TTS provayderini quradi."""
    if settings.mock_mode:
        return FakeTTS()
    provider = settings.tts_provider.lower()
    if provider == "edge_tts":
        return EdgeTTS(voice=settings.tts_voice)
    if provider == "elevenlabs":
        return ElevenLabsTTS(secrets.get(_TTS_KEY) or "", voice_id=settings.voice_id)
    if provider == "mock":
        return FakeTTS()
    raise ConfigError(f"Noma'lum TTS provider: '{settings.tts_provider}'")


def build_vad(settings: VoiceSettings) -> VoiceActivityDetector:
    """Config nomiga qarab VAD provayderini quradi."""
    if settings.mock_mode:
        return FakeVAD()
    provider = settings.vad_provider.lower()
    if provider == "energy":
        return EnergyVAD()
    if provider == "silero":
        return SileroVAD(sample_rate=settings.sample_rate)
    if provider == "mock":
        return FakeVAD()
    raise ConfigError(f"Noma'lum VAD provider: '{settings.vad_provider}'")


def build_audio_input(settings: VoiceSettings) -> AudioInput:
    """OS (yoki config)ga qarab mikrofon provayderini quradi."""
    if settings.mock_mode:
        return FakeAudioInput()
    target = settings.audio_provider.lower()
    if target == "auto":
        target = _detect_os()
    if target == "macos":
        return MacRecorder()
    if target == "linux":
        return LinuxRecorder()
    if target == "windows":
        return WindowsRecorder()
    if target == "mock":
        return FakeAudioInput()
    raise ConfigError(f"Noma'lum audio provider: '{settings.audio_provider}'")


def build_audio_output(settings: VoiceSettings) -> AudioOutput:
    """OS (yoki config)ga qarab karnay provayderini quradi."""
    if settings.mock_mode:
        return FakeAudioOutput()
    target = settings.audio_provider.lower()
    if target == "auto":
        target = _detect_os()
    if target == "macos":
        return MacPlayer()
    if target == "linux":
        return LinuxPlayer()
    if target == "windows":
        return WindowsPlayer()
    if target == "mock":
        return FakeAudioOutput()
    raise ConfigError(f"Noma'lum audio provider: '{settings.audio_provider}'")
