"""``FakeSystemSampler`` — belgilangan tizim-statistikasini qaytaradigan soxta sampler."""

from __future__ import annotations

from code.doda.core.models.telemetry import SystemStats


class FakeSystemSampler:
    """Test uchun oldindan belgilangan ``SystemStats`` qaytaradi."""

    def __init__(self, stats: SystemStats | None = None) -> None:
        self._stats = stats or SystemStats(cpu_percent=10.0, memory_percent=20.0, disk_percent=30.0)

    async def sample(self) -> SystemStats:
        return self._stats
