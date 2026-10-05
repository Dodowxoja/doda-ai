"""Muhit (environment) sensorlari — clock/clipboard/active-window (EnvSensor port ortida)."""

from __future__ import annotations

from code.doda.providers.env.active_window import ActiveWindowSensor
from code.doda.providers.env.clipboard import ClipboardSensor
from code.doda.providers.env.clock import ClockSensor
from code.doda.providers.env.fake import FakeEnvSensor

__all__ = ["ActiveWindowSensor", "ClipboardSensor", "ClockSensor", "FakeEnvSensor"]
