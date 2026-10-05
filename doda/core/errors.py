"""DODA domen xatolari (core qatlami) — tashqi kutubxonaga bog'liq EMAS.

Barcha DODA xatolari :class:`DodaError`dan meros oladi. Bu qatlamlar bo'ylab bir xil
xato-ishlovni beradi (masalan, xatoni Event Bus'ga ``error`` hodisasi sifatida chiqarish).
Har bir modul o'z aniqroq xatosini shu iyerarxiyaga qo'shadi.
"""

from __future__ import annotations


class DodaError(Exception):
    """DODA'dagi barcha domen xatolarining bazasi.

    Standart :class:`Exception` o'rniga shundan meros olinadi — bu tashqi/kutilmagan
    xatolarni DODA'ning o'z (kutilgan) xatolaridan ajratishga imkon beradi.
    """


class ConfigError(DodaError):
    """Konfiguratsiya noto'g'ri, yetishmayapti yoki nomuvofiq bo'lganda."""


class SecretNotFoundError(DodaError):
    """So'ralgan sir (secret) mavjud emasligida (masalan API kalit qo'yilmagan)."""


class ProviderError(DodaError):
    """Provider (LLM/Vision/Memory/… adapter) darajasidagi xato.

    Konkret providerlar shundan aniqroq xato meros oladi (masalan ``LLMTimeoutError``).
    """


class LLMError(ProviderError):
    """LLM provayderi so'rovni bajara olmaganda (API xatosi, timeout va h.k.)."""


class LLMUnavailableError(LLMError):
    """LLM provayderi mavjud emas (kalit yo'q yoki hali qo'llab-quvvatlanmaydi)."""


class SpeechError(ProviderError):
    """Ovoz (STT/TTS/VAD/audio) provayderi darajasidagi xato."""


class STTError(SpeechError):
    """Nutqni matnga aylantirishda xato (transkripsiya)."""


class TTSError(SpeechError):
    """Matnni nutqqa aylantirishda xato (sintez)."""


class VADError(SpeechError):
    """Ovoz-faollikni aniqlashda xato."""


class AudioError(SpeechError):
    """Audio kirish/chiqishda xato (mikrofon/karnay)."""
