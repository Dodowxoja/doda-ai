"""``FakeEnvSensor`` — deterministik test-sensori."""

from __future__ import annotations

from code.doda.core.errors import DodaError


class FakeEnvSensor:
    """EnvSensor portining soxta implementatsiyasi (test uchun)."""

    def __init__(self, *, name: str = "fake", value: str = "qiymat", fail: bool = False) -> None:
        self._name = name
        self._value = value
        self._fail = fail

    @property
    def name(self) -> str:
        return self._name

    async def read(self) -> str:
        if self._fail:
            raise DodaError(f"{self._name} sensori xato berdi")
        return self._value
