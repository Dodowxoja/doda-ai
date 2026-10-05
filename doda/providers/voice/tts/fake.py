"""Soxta TTS (mock mode / test uchun)."""

from __future__ import annotations


class FakeTTS:
    """Matnni oldindan aytib bo'ladigan audio-baytlarga aylantiruvchi soxta TTS."""

    def __init__(self) -> None:
        self.spoken: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.spoken.append(text)
        return f"audio:{text}".encode()
