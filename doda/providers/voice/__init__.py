"""Ovoz provayderlari — STT / TTS / VAD / audio / wake subpaketlari + registry.

Yangi imkoniyat = tegishli subpaket ichida yangi adapter + ``registry`` ga tarmoq (core
o'zgarmaydi). ``mock_mode`` yoqilsa barchasi soxta (kalitsiz test/ishlash). Bu modul barcha
provayderlarni bitta barqaror import yuzasiga jamlaydi (container/testlar shu yerdan oladi).
"""

from doda.providers.voice.audio import (
    AfplayOutput,
    FakeAudioInput,
    FakeAudioOutput,
    FakeStreamingAudioInput,
    FfmpegRecorder,
    FrameStreamAdapter,
    LinuxPlayer,
    LinuxRecorder,
    MacPlayer,
    MacRecorder,
    WindowsPlayer,
    WindowsRecorder,
)
from doda.providers.voice.registry import (
    build_audio_input,
    build_audio_output,
    build_stt,
    build_tts,
    build_vad,
)
from doda.providers.voice.runner import FileRunner, subprocess_to_file
from doda.providers.voice.stt import ElevenLabsSTT, FakeStreamingSTT, FakeSTT, WhisperSTT
from doda.providers.voice.tts import DEFAULT_VOICE, EdgeTTS, ElevenLabsTTS, FakeTTS
from doda.providers.voice.vad import EnergyVAD, FakeVAD, SileroVAD
from doda.providers.voice.wake import FakeWakeWord, KeywordWakeDetector

__all__ = [
    "DEFAULT_VOICE",
    "AfplayOutput",
    "EdgeTTS",
    "ElevenLabsSTT",
    "ElevenLabsTTS",
    "EnergyVAD",
    "FakeAudioInput",
    "FakeAudioOutput",
    "FakeSTT",
    "FakeStreamingAudioInput",
    "FakeStreamingSTT",
    "FakeTTS",
    "FakeVAD",
    "FakeWakeWord",
    "FfmpegRecorder",
    "FileRunner",
    "FrameStreamAdapter",
    "KeywordWakeDetector",
    "LinuxPlayer",
    "LinuxRecorder",
    "MacPlayer",
    "MacRecorder",
    "SileroVAD",
    "WhisperSTT",
    "WindowsPlayer",
    "WindowsRecorder",
    "build_audio_input",
    "build_audio_output",
    "build_stt",
    "build_tts",
    "build_vad",
    "subprocess_to_file",
]
