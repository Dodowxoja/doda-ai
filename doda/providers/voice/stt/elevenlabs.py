"""``ElevenLabsSTT`` — ElevenLabs Scribe STT adapteri (bir martalik).

O'ZBEK TILI OGOHLANTIRISHI: ElevenLabs o'zbek tilini native darajada qo'llab-quvvatlashi
kafolatlanmagan — sifat provider hujjatiga bog'liq. Shuning uchun bu DEFAULT emas; config
(``voice.stt_provider``) orqali tanlanadi va yetarli bo'lmasa boshqa providerga qaytiladi
(``registry`` fallback). Kalit ``SecretStore`` da (``speech.stt.key``), kodda EMAS.

``elevenlabs`` kutubxonasi ixtiyoriy: o'rnatilmagan bo'lsa aniq ``STTError`` beriladi (crash
emas). Real API chaqiruvlari test qamrovidan tashqarida (#pragma). Realtime WebSocket STT → v1.1.
"""

from __future__ import annotations

from typing import Any

from doda.core.errors import STTError

#: O'zbek tili sifati noaniq bo'lgan tillar (registry ogohlantirish logi uchun; rad ETMAYDI).
UNCERTAIN_LANGUAGES = frozenset({"uz"})


class ElevenLabsSTT:
    """ElevenLabs Scribe orqali STT (bir martalik)."""

    def __init__(self, api_key: str, *, model: str = "scribe_v1", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def _client(self) -> Any:
        """ElevenLabs mijozini lazy quradi; kutubxona yo'q bo'lsa ``STTError``."""
        try:
            from elevenlabs.client import ElevenLabs  # type: ignore[import-not-found]
        except ImportError as exc:
            raise STTError(
                "elevenlabs kutubxonasi o'rnatilmagan (pip install 'doda[voice]')"
            ) from exc
        return ElevenLabs(api_key=self._api_key)  # pragma: no cover

    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        """Audio'ni matnga aylantiradi (bir martalik)."""
        if not self._api_key:
            raise STTError("ElevenLabs API kaliti yo'q (SecretStore: speech.stt.key)")
        client = self._client()
        return await self._transcribe_via_client(client, audio, language)  # pragma: no cover

    async def _transcribe_via_client(  # pragma: no cover
        self, client: Any, audio: bytes, language: str
    ) -> str:
        import asyncio
        import io

        def _call() -> str:
            result = client.speech_to_text.convert(
                file=io.BytesIO(audio), model_id=self._model, language_code=language
            )
            return str(getattr(result, "text", "")).strip()

        return await asyncio.to_thread(_call)
