"""``SileroVAD`` — Silero (torch) asosidagi neyron VAD (ixtiyoriy, yuqori aniqlik).

``torch``/``silero-vad`` ixtiyoriy: o'rnatilmagan bo'lsa aniq ``VADError`` (crash emas) —
``registry`` energiya-VAD'ga qaytadi. Model yuklash/inference #pragma (og'ir, tarmoq/torch
talab qiladi; gate'da ishlamaydi). Config: ``voice.vad_provider=silero``.
"""

from __future__ import annotations

from typing import Any

from code.doda.core.errors import VADError


class SileroVAD:
    """Silero neyron VAD (lazy torch)."""

    def __init__(self, *, threshold: float = 0.5, sample_rate: int = 16000) -> None:
        self._threshold = threshold
        self._sample_rate = sample_rate
        self._model: Any = None

    def _ensure_model(self) -> Any:
        """Silero modelini lazy yuklaydi; torch yo'q bo'lsa ``VADError``."""
        if self._model is not None:  # pragma: no cover
            return self._model
        try:
            import torch  # type: ignore[import-not-found]
        except ImportError as exc:
            raise VADError("torch/silero o'rnatilmagan (pip install 'doda[voice-silero]')") from exc
        model, _ = torch.hub.load(  # pragma: no cover
            "snakers4/silero-vad", "silero_vad", trust_repo=True
        )
        self._model = model  # pragma: no cover
        return self._model  # pragma: no cover

    async def is_speech(self, frame: bytes) -> bool:
        """``frame`` nutqmi (Silero ehtimolligi ≥ threshold)."""
        model = self._ensure_model()
        return await self._infer(model, frame)  # pragma: no cover

    async def _infer(self, model: Any, frame: bytes) -> bool:  # pragma: no cover
        import asyncio

        import torch

        def _call() -> bool:
            tensor = torch.frombuffer(bytearray(frame), dtype=torch.int16).float() / 32768.0
            prob = float(model(tensor, self._sample_rate).item())
            return prob >= self._threshold

        return await asyncio.to_thread(_call)

    def reset(self) -> None:
        """Model holatini tozalaydi (yangi sessiya uchun)."""
        if self._model is not None and hasattr(self._model, "reset_states"):  # pragma: no cover
            self._model.reset_states()
