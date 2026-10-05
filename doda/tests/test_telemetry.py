"""Telemetriya testlari — model + FakeSystemSampler + TelemetryService."""

from __future__ import annotations

from datetime import datetime

from doda.core.models.event import Event
from doda.core.models.telemetry import SystemStats, TelemetrySnapshot
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability
from doda.providers.telemetry import FakeSystemSampler, PsutilSampler
from doda.telemetry import TelemetryService

_NOW = datetime(2026, 8, 9, 12, 0, 0)


class StaticMetrics:
    """Belgilangan metrikalarni qaytaradigan soxta MetricsReader."""

    def __init__(self, metrics: dict[str, float]) -> None:
        self._metrics = metrics

    def snapshot(self) -> dict[str, float]:
        return dict(self._metrics)


# ---------------- Modellar ----------------


def test_snapshot_defaults() -> None:
    snap = TelemetrySnapshot(system=SystemStats())
    assert snap.health == "ok"
    assert snap.metrics == {}


# ---------------- TelemetryService ----------------


async def test_snapshot_gathers_system_and_metrics() -> None:
    service = TelemetryService(
        StaticMetrics({"tokens": 42.0}),
        FakeSystemSampler(SystemStats(cpu_percent=10.0, memory_percent=20.0)),
        now=lambda: _NOW,
    )
    snap = await service.snapshot()
    assert snap.system.cpu_percent == 10.0
    assert snap.metrics == {"tokens": 42.0}
    assert snap.health == "ok"
    assert snap.timestamp == _NOW


async def test_health_degraded_on_high_usage() -> None:
    service = TelemetryService(
        StaticMetrics({}), FakeSystemSampler(SystemStats(cpu_percent=99.0)), now=lambda: _NOW
    )
    snap = await service.snapshot()
    assert snap.health == "degraded"


async def test_uses_real_observability_metrics() -> None:
    obs = BasicObservability()
    obs.metric("llm.tokens", 5.0)
    obs.metric("llm.tokens", 3.0)
    service = TelemetryService(obs, FakeSystemSampler(), observability=obs)
    snap = await service.snapshot()
    assert snap.metrics["llm.tokens"] == 8.0


async def test_psutil_sampler_returns_stats() -> None:
    # Real sampler (psutil o'rnatilgan yoki yo'q) — SystemStats qaytarishi kifoya.
    stats = await PsutilSampler().sample()
    assert isinstance(stats, SystemStats)
    assert 0.0 <= stats.cpu_percent <= 100.0


async def test_emits_snapshot_event() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.payload["health"])

    events.subscribe("telemetry.snapshot", handler)
    service = TelemetryService(StaticMetrics({}), FakeSystemSampler(), events=events)
    await service.snapshot()
    assert seen == ["ok"]
