"""Env sensorlar testlari — contract + soxta runner bilan buyruq tekshiruvi."""

from __future__ import annotations

from collections.abc import Sequence

from code.doda.core.interfaces.perception import EnvSensor
from code.doda.providers.env import (
    ActiveWindowSensor,
    ClipboardSensor,
    ClockSensor,
    FakeEnvSensor,
)
from code.doda.tests.contracts.env_sensor_contract import EnvSensorContract


async def _text_runner(command: Sequence[str]) -> str:
    return "natija"


class TestFakeEnvSensor(EnvSensorContract):
    def make_sensor(self) -> EnvSensor:
        return FakeEnvSensor()


class TestClockSensor(EnvSensorContract):
    def make_sensor(self) -> EnvSensor:
        return ClockSensor()

    async def test_returns_iso_time(self) -> None:
        assert "T" in await ClockSensor().read()


class TestClipboardSensor(EnvSensorContract):
    def make_sensor(self) -> EnvSensor:
        return ClipboardSensor(runner=_text_runner)

    async def test_uses_pbpaste(self) -> None:
        captured: dict[str, list[str]] = {}

        async def runner(command: Sequence[str]) -> str:
            captured["cmd"] = list(command)
            return "matn"

        assert await ClipboardSensor(runner=runner).read() == "matn"
        assert captured["cmd"] == ["pbpaste"]

    async def test_truncates_long_text(self) -> None:
        async def runner(command: Sequence[str]) -> str:
            return "x" * 1000

        assert len(await ClipboardSensor(runner=runner).read()) == 500


class TestActiveWindowSensor(EnvSensorContract):
    def make_sensor(self) -> EnvSensor:
        return ActiveWindowSensor(runner=_text_runner)

    async def test_strips_output(self) -> None:
        async def runner(command: Sequence[str]) -> str:
            return "Safari\n"

        assert await ActiveWindowSensor(runner=runner).read() == "Safari"
