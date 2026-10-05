"""DOMEN qatlami — sof biznes-mantiq (portlar + modellar + xatolar).

Tashqi kutubxonaga BOG'LIQ EMAS (Dependency Rule): core hech narsani import qilmaydi
tashqaridan. Application faqat core'ni biladi; Infrastructure core portlarini implement qiladi.
"""

from __future__ import annotations

from doda.core.errors import (
    AudioError,
    ConfigError,
    DodaError,
    LLMError,
    LLMUnavailableError,
    ProviderError,
    SecretNotFoundError,
    SpeechError,
    STTError,
    TTSError,
    VADError,
)

__all__ = [
    "AudioError",
    "ConfigError",
    "DodaError",
    "LLMError",
    "LLMUnavailableError",
    "ProviderError",
    "STTError",
    "SecretNotFoundError",
    "SpeechError",
    "TTSError",
    "VADError",
]
