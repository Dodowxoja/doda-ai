"""``build_vision_provider`` — config nomiga qarab kamera provayderini quradi."""

from __future__ import annotations

from doda.core.errors import ConfigError
from doda.core.interfaces.perception import VisionProvider
from doda.providers.vision.mac_camera import MacCameraProvider
from doda.providers.vision.screen import ScreenCaptureProvider

_UNIMPLEMENTED = frozenset({"usb", "rtsp", "ip"})


def build_vision_provider(name: str) -> VisionProvider:
    """Kamera nomiga qarab VisionProvider qaytaradi.

    Raises:
        ConfigError: Kamera turi noma'lum yoki hali qo'llab-quvvatlanmaydi (usb/rtsp/ip → v2.0).
    """
    key = name.lower()
    if key == "screen":
        return ScreenCaptureProvider()
    if key in ("mac", "mac_camera", "camera"):
        return MacCameraProvider()
    if key in _UNIMPLEMENTED:
        raise ConfigError(f"Kamera turi '{name}' hali qo'llab-quvvatlanmaydi (v2.0)")
    raise ConfigError(f"Noma'lum kamera turi: '{name}'")
