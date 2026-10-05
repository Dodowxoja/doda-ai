"""Perception (sezgi) portlari — ``VisionProvider`` va ``EnvSensor``.

Perception qatlami DODA'ning "sezgilari": ko'rish (kamera/ekran) va muhit (clipboard, vaqt,
aktiv oyna va h.k.). Har sezgi bitta port ortida — kamera almashtirilsa (mac/usb/ip) yoki yangi
sensor qo'shilsa, agent va servislar o'zgarmaydi.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from code.doda.core.models.media import MediaFrame


@runtime_checkable
class VisionProvider(Protocol):
    """Ko'rish manbai (kamera/ekran) — bitta kadr oladi."""

    @property
    def name(self) -> str:
        """Manba nomi (masalan ``"screen"``, ``"mac_camera"``)."""
        ...

    async def capture(self) -> MediaFrame:
        """Joriy kadrni oladi va qaytaradi."""
        ...


@runtime_checkable
class EnvSensor(Protocol):
    """Muhit sensori — bitta o'qiladigan qiymat (vaqt, clipboard, aktiv oyna...)."""

    @property
    def name(self) -> str:
        """Sensor nomi (masalan ``"clock"``, ``"clipboard"``)."""
        ...

    async def read(self) -> str:
        """Sensorning joriy qiymatini (matn) qaytaradi."""
        ...
