"""Telemetriya portlari — ``SystemSampler`` va ``MetricsReader``.

``SystemSampler`` tizim resurslarini o'lchaydi (CPU/RAM/disk); ``MetricsReader`` yig'ilgan
metrikalarni beradi (BasicObservability bularni M1'dan to'playdi). ``TelemetryService`` (M14)
ikkalasini birlashtiradi. Konkret implementatsiyalar ``doda/providers/telemetry/`` da.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from code.doda.core.models.telemetry import SystemStats


@runtime_checkable
class SystemSampler(Protocol):
    """Tizim resurslaridan foydalanishni o'lchaydi."""

    async def sample(self) -> SystemStats:
        """Joriy CPU/RAM/disk foizlarini qaytaradi."""
        ...


@runtime_checkable
class MetricsReader(Protocol):
    """Yig'ilgan metrikalar suratini beradi (nom→qiymat)."""

    def snapshot(self) -> Mapping[str, float]:
        """Joriy metrikalar suratini qaytaradi."""
        ...
