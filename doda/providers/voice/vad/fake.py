"""Soxta VAD (mock mode / test uchun)."""

from __future__ import annotations

from collections.abc import Sequence


class FakeVAD:
    """Belgilangan natija(lar)ni qaytaradigan soxta VAD."""

    def __init__(self, results: bool | Sequence[bool] = True) -> None:
        self._fixed = results if isinstance(results, bool) else None
        self._sequence = list(results) if not isinstance(results, bool) else []
        self._i = 0
        self.resets = 0

    async def is_speech(self, frame: bytes) -> bool:
        if self._fixed is not None:
            return self._fixed
        result = self._sequence[min(self._i, len(self._sequence) - 1)]
        self._i += 1
        return result

    def reset(self) -> None:
        self.resets += 1
        self._i = 0
