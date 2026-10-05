"""``EnergyVAD` — kutubxonasiz (energiya/RMS asosidagi) ovoz-faollik detektori.

16-bit PCM kadrining RMS amplitudasini hisoblab, chegaradan yuqori bo'lsa "nutq" deydi.
Hech qanday tashqi kutubxona (torch/webrtc) talab qilmaydi — 24/7 lokal ishlash uchun ideal
(default VAD). Nozikroq aniqlik kerak bo'lsa ``SileroVAD`` config orqali tanlanadi.
"""

from __future__ import annotations

import math
from array import array


class EnergyVAD:
    """RMS-energiya asosidagi oddiy VAD (16-bit PCM kutadi)."""

    def __init__(self, *, threshold: float = 500.0) -> None:
        """VAD quradi.

        Args:
            threshold: Nutq deb hisoblanadigan eng kichik RMS amplituda (0..32767).
        """
        self._threshold = threshold

    async def is_speech(self, frame: bytes) -> bool:
        """``frame`` (16-bit PCM) nutq o'z ichiga oladimi (RMS ≥ threshold)."""
        usable = len(frame) - (len(frame) % 2)
        if usable < 2:
            return False
        samples = array("h")
        samples.frombytes(frame[:usable])
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
        return rms >= self._threshold

    def reset(self) -> None:
        """Holatsiz — tozalash shart emas (interfeys uchun)."""
