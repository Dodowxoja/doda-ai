"""Subpaket ``base.py`` re-eksportlari to'g'ri portlarni ochishini tekshiradi."""

from __future__ import annotations

from code.doda.core.interfaces import voice as ports
from code.doda.providers.voice.audio import base as audio_base
from code.doda.providers.voice.stt import base as stt_base
from code.doda.providers.voice.tts import base as tts_base
from code.doda.providers.voice.vad import base as vad_base
from code.doda.providers.voice.wake import base as wake_base


def test_base_modules_reexport_ports() -> None:
    assert stt_base.SpeechToText is ports.SpeechToText
    assert stt_base.StreamingSpeechToText is ports.StreamingSpeechToText
    assert tts_base.TextToSpeech is ports.TextToSpeech
    assert vad_base.VoiceActivityDetector is ports.VoiceActivityDetector
    assert wake_base.WakeWordDetector is ports.WakeWordDetector
    assert audio_base.AudioInput is ports.AudioInput
    assert audio_base.AudioOutput is ports.AudioOutput
    assert audio_base.StreamingAudioInput is ports.StreamingAudioInput
