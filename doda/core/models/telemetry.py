"""Telemetriya domen modellari — ``SystemStats`` / ``TelemetrySnapshot``.

Tizim resurslari (CPU/RAM/disk) va yig'ilgan metrikalar (token/xarajat/asbob-plugin
statistikasi) bitta suratga jamlanadi. Modellar frozen — sof domen.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SystemStats:
    """Tizim resurslaridan foydalanish (foizlarda)."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    """Bir lahzalik telemetriya surati (tizim + metrikalar + salomatlik)."""

    system: SystemStats
    metrics: Mapping[str, float] = field(default_factory=dict)
    health: str = "ok"
    timestamp: datetime = field(default_factory=datetime.now)
