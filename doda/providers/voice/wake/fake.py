"""Soxta wake-detektor (mock mode / test uchun)."""

from __future__ import annotations


class FakeWakeWord:
    """Darhol "aniqlandi" deb qaytaradigan soxta wake-detektor."""

    def __init__(self) -> None:
        self.waited = 0

    async def wait_for_wake(self) -> None:
        self.waited += 1
