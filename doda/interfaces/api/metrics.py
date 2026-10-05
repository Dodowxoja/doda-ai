"""``MetricsPump` — telemetriyani davriy ravishda ``system.metrics`` eventi sifatida uzatadi.

``TelemetryService`` suratini olib, dashboard kutadigan shaklga aylantiradi va ``EventBridge``
orqali barcha klientlarga yuboradi. Davomiy sikl (``run``) delivery serverida ishlaydi; bitta
qadam (``pump_once``) deterministik test uchun ajratilgan.
"""

from __future__ import annotations

from typing import Protocol

from doda.core.models.telemetry import TelemetrySnapshot

_RAM_TOTAL_GB = 16.0
_DISK_TOTAL_GB = 512.0


class _Telemetry(Protocol):
    async def snapshot(self) -> TelemetrySnapshot: ...


class _Broadcaster(Protocol):
    async def broadcast(self, event: str, data: dict[str, float]) -> None: ...


class MetricsPump:
    """Telemetriya suratini ``system.metrics`` eventiga aylantirib uzatuvchi."""

    def __init__(self, telemetry: _Telemetry, broadcaster: _Broadcaster) -> None:
        self._telemetry = telemetry
        self._broadcaster = broadcaster

    async def pump_once(self) -> None:
        """Bitta telemetriya suratini olib, dashboard shaklida uzatadi."""
        snap = await self._telemetry.snapshot()
        sys = snap.system
        data: dict[str, float] = {
            "cpu": round(sys.cpu_percent),
            "ram": round(sys.memory_percent),
            "disk": round(sys.disk_percent),
            "net": round(snap.metrics.get("net_kbps", 0.0)),
            "ramUsed": round(sys.memory_percent / 100 * _RAM_TOTAL_GB, 1),
            "ramTotal": _RAM_TOTAL_GB,
            "diskUsed": round(sys.disk_percent / 100 * _DISK_TOTAL_GB),
            "diskTotal": _DISK_TOTAL_GB,
            "netDown": round(snap.metrics.get("net_down_kbps", 0.0)),
            "netUp": round(snap.metrics.get("net_up_bps", 0.0)),
        }
        await self._broadcaster.broadcast("system.metrics", data)
