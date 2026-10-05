"""``EnvSensor`` porti uchun contract."""

from __future__ import annotations

from doda.core.interfaces.perception import EnvSensor


class EnvSensorContract:
    """EnvSensor kelishuvi (subklass ``make_sensor()``ni beradi)."""

    def make_sensor(self) -> EnvSensor:
        raise NotImplementedError

    def test_name_is_nonempty(self) -> None:
        assert self.make_sensor().name != ""

    async def test_read_returns_string(self) -> None:
        value = await self.make_sensor().read()
        assert isinstance(value, str)
