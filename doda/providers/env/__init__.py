"""Muhit (environment) sensorlari — clock/clipboard/active-window (EnvSensor port ortida)."""

from __future__ import annotations

from doda.providers.env.active_window import ActiveWindowSensor
from doda.providers.env.clipboard import ClipboardSensor
from doda.providers.env.clock import ClockSensor
from doda.providers.env.fake import FakeEnvSensor

__all__ = ["ActiveWindowSensor", "ClipboardSensor", "ClockSensor", "FakeEnvSensor"]
