"""``TelemetryService`` — tizim va foydalanish metrikalarini bitta suratga jamlaydi.

Tizim resurslari (``SystemSampler``) + yig'ilgan metrikalar (``MetricsReader``: token/xarajat/
asbob-plugin statistikasi) + salomatlik holati → ``TelemetrySnapshot``. ``telemetry.snapshot``
eventi chiqadi (monitoring dashboard uchun).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.telemetry import MetricsReader, SystemSampler
from code.doda.core.models.event import Event
from code.doda.core.models.telemetry import TelemetrySnapshot

_SOURCE = "telemetry"
_HEALTH_THRESHOLD = 95.0


class TelemetryService:
    """Tizim + foydalanish telemetriyasini jamlovchi servis."""

    def __init__(
        self,
        metrics: MetricsReader,
        sampler: SystemSampler,
        *,
        events: EventBus | None = None,
        now: Callable[[], datetime] = datetime.now,
        observability: Observability | None = None,
    ) -> None:
        self._metrics = metrics
        self._sampler = sampler
        self._events = events
        self._now = now
        self._obs = observability

    async def snapshot(self) -> TelemetrySnapshot:
        """Joriy telemetriya suratini yig'adi (salomatlik bilan)."""
        system = await self._sampler.sample()
        degraded = (
            system.cpu_percent >= _HEALTH_THRESHOLD
            or system.memory_percent >= _HEALTH_THRESHOLD
            or system.disk_percent >= _HEALTH_THRESHOLD
        )
        health = "degraded" if degraded else "ok"
        snapshot = TelemetrySnapshot(
            system=system,
            metrics=dict(self._metrics.snapshot()),
            health=health,
            timestamp=self._now(),
        )
        if self._obs is not None:
            self._obs.log("info", "telemetry snapshot", health=health)
        if self._events is not None:
            await self._events.publish(
                Event(name="telemetry.snapshot", payload={"health": health}, source=_SOURCE)
            )
        return snapshot
