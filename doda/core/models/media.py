"""``MediaFrame`` — kameradan/ekrandan olingan bitta kadr (immutable)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MediaFrame:
    """Bitta media kadri (rasm).

    Attributes:
        media_type: MIME turi (masalan ``"image/png"``, ``"image/jpeg"``).
        data: Xom baytlar.
        source: Manba nomi (masalan ``"screen"``, ``"mac_camera"``).
    """

    media_type: str
    data: bytes
    source: str = ""
