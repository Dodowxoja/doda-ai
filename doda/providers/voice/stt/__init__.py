"""STT provayderlari — Whisper (default) + ElevenLabs (ixtiyoriy) + soxta."""

from code.doda.providers.voice.stt.elevenlabs import ElevenLabsSTT
from code.doda.providers.voice.stt.fake import FakeStreamingSTT, FakeSTT
from code.doda.providers.voice.stt.whisper import WhisperSTT

__all__ = ["ElevenLabsSTT", "FakeSTT", "FakeStreamingSTT", "WhisperSTT"]
