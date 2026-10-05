"""``PsutilSampler`` — ``psutil`` orqali real tizim-resurslarini o'lchaydi.

``psutil`` ixtiyoriy bog'liqlik: mavjud bo'lmasa yoki o'lchash imkoni bo'lmasa, nollar
qaytadi (telemetriya buzilmasin). Bloklovchi o'lchash ``asyncio.to_thread`` orqali.
"""

from __future__ import annotations

import asyncio

from doda.core.models.telemetry import SystemStats


class PsutilSampler:
    """Real tizim statistikasini ``psutil`` bilan o'lchaydi (yo'q bo'lsa nollar)."""

    async def sample(self) -> SystemStats:
        return await asyncio.to_thread(self._sample_sync)

    def _sample_sync(self) -> SystemStats:  # pragma: no cover
        try:
            import psutil  # type: ignore[import-untyped]
        except ImportError:
            return SystemStats()
        return SystemStats(
            cpu_percent=float(psutil.cpu_percent(interval=None)),
            memory_percent=float(psutil.virtual_memory().percent),
            disk_percent=float(psutil.disk_usage("/").percent),
        )
