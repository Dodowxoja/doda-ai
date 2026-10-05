"""``ElevenLabsTTS`` — ElevenLabs TTS adapteri (ixtiyoriy, default emas).

O'ZBEK TILI OGOHLANTIRISHI: ElevenLabs ovozlari o'zbekchani tabiiy talaffuz qilishi
kafolatlanmagan — shuning uchun DEFAULT edge-tts (uz-UZ-*). Config (``voice.tts_provider``)
orqali tanlanadi. Kalit ``SecretStore`` da (``speech.tts.key``). ``elevenlabs`` kutubxonasi
ixtiyoriy: yo'q bo'lsa aniq ``TTSError`` (crash emas). Real API chaqiruvi #pragma.
"""

from __future__ import annotations

from typing import Any

from code.doda.core.errors import TTSError


class ElevenLabsTTS:
    """ElevenLabs orqali matndan ovoz (mp3)."""

    def __init__(
        self, api_key: str, *, voice_id: str = "", model: str = "eleven_multilingual_v2"
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model = model

    def _client(self) -> Any:
        """ElevenLabs mijozini lazy quradi; kutubxona yo'q bo'lsa ``TTSError``."""
        try:
            from elevenlabs.client import ElevenLabs  # type: ignore[import-not-found]
        except ImportError as exc:
            raise TTSError(
                "elevenlabs kutubxonasi o'rnatilmagan (pip install 'doda[voice]')"
            ) from exc
        return ElevenLabs(api_key=self._api_key)  # pragma: no cover

    async def synthesize(self, text: str) -> bytes:
        """Matndan audio (mp3 baytlar) yaratadi."""
        if not self._api_key:
            raise TTSError("ElevenLabs API kaliti yo'q (SecretStore: speech.tts.key)")
        if not self._voice_id:
            raise TTSError("ElevenLabs voice_id yo'q (config: voice.voice_id)")
        client = self._client()
        return await self._synthesize_via_client(client, text)  # pragma: no cover

    async def _synthesize_via_client(self, client: Any, text: str) -> bytes:  # pragma: no cover
        import asyncio

        def _call() -> bytes:
            stream = client.text_to_speech.convert(
                voice_id=self._voice_id, model_id=self._model, text=text
            )
            return b"".join(stream)

        return await asyncio.to_thread(_call)
