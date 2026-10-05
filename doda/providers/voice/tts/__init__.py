"""TTS provayderlari — EdgeTTS (default, o'zbek) + ElevenLabs (ixtiyoriy) + soxta."""

from code.doda.providers.voice.tts.edge_tts import DEFAULT_VOICE, EdgeTTS
from code.doda.providers.voice.tts.elevenlabs import ElevenLabsTTS
from code.doda.providers.voice.tts.fake import FakeTTS

__all__ = ["DEFAULT_VOICE", "EdgeTTS", "ElevenLabsTTS", "FakeTTS"]
