"""Wake-so'z detektorlari — STT-asosli (default) + soxta. Maxsus engine → v1.1."""

from code.doda.providers.voice.wake.fake import FakeWakeWord
from code.doda.providers.voice.wake.keyword import KeywordWakeDetector

__all__ = ["FakeWakeWord", "KeywordWakeDetector"]
