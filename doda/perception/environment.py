"""``EnvironmentService`` — muhit sensorlarini yig'ib, kontekst-snapshot beradi.

Yoqilgan sensorlarni (clock/clipboard/active-window...) o'qib, bitta lug'atga jamlaydi va
``perception.env`` eventini chiqaradi. Bitta sensor xato bersa, boshqalari ishlaydi (izolyatsiya).
"""

from __future__ import annotations

from collections.abc import Sequence

from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.perception import EnvSensor
from code.doda.core.models.event import Event

_SOURCE = "environment"


class EnvironmentService:
    """Muhit sensorlarini jamlaydigan servis."""

    def __init__(
        self,
        sensors: Sequence[EnvSensor],
        events: EventBus,
        observability: Observability | None = None,
    ) -> None:
        self._sensors = tuple(sensors)
        self._events = events
        self._obs = observability

    async def snapshot(self) -> dict[str, str]:
        """Barcha sensorlarni o'qib, ``{sensor_nomi: qiymat}`` snapshot qaytaradi."""
        result: dict[str, str] = {}
        for sensor in self._sensors:
            try:
                result[sensor.name] = await sensor.read()
            except Exception as exc:  # bitta sensor xatosi butun snapshot'ni buzmasin
                result[sensor.name] = f"(xato: {exc})"
                if self._obs is not None:
                    self._obs.log("warning", f"sensor '{sensor.name}' xato berdi", error=repr(exc))
        await self._events.publish(
            Event(name="perception.env", payload={"snapshot": result}, source=_SOURCE)
        )
        return result
