"""VOICE qatlami — ovoz quvuri (wake → STT → Agent → TTS → karnay) + realtime.

``VoicePipeline`` — sodda bir navbatli quvur (M8). ``RealtimeVoiceSession`` — VAD-boshqariladigan
realtime suhbat (barge-in bilan). ``VoiceSession`` — holat-mashina. Konkret ovoz portlari
``doda/providers/voice/`` da; bu qatlam ularni birlashtiradi.
"""

from doda.voice.language import detect_language
from doda.voice.pipeline import VoicePipeline
from doda.voice.realtime import RealtimeVoiceSession
from doda.voice.session import VoiceSession

__all__ = ["RealtimeVoiceSession", "VoicePipeline", "VoiceSession", "detect_language"]
