"""``MetricsPump`` + ``APIServer`` wiring testi."""

from __future__ import annotations

from doda.container import build_container
from doda.core.models.telemetry import SystemStats, TelemetrySnapshot
from doda.interfaces.api import APIServer, MetricsPump
from doda.interfaces.api.server import default_static_dir


class FakeTelemetry:
    async def snapshot(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            system=SystemStats(cpu_percent=42.0, memory_percent=50.0, disk_percent=25.0),
            metrics={"net_kbps": 128.0},
            health="ok",
        )


class SpyBroadcaster:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, float]]] = []

    async def broadcast(self, event: str, data: dict[str, float]) -> None:
        self.sent.append((event, data))


async def test_metrics_pump_maps_snapshot() -> None:
    spy = SpyBroadcaster()
    await MetricsPump(FakeTelemetry(), spy).pump_once()
    assert spy.sent[0][0] == "system.metrics"
    data = spy.sent[0][1]
    assert data["cpu"] == 42
    assert data["ram"] == 50
    assert data["disk"] == 25
    assert data["ramUsed"] == 8.0  # 50% * 16GB


def test_server_wires_components() -> None:
    server = APIServer(build_container())
    assert server.bridge is not None
    assert server.commands is not None
    assert server.metrics is not None
    assert server.ws_url == "ws://127.0.0.1:8765/ws"
    assert server.url == "http://127.0.0.1:8765/"


def test_default_static_dir_has_dashboard() -> None:
    d = default_static_dir()
    assert d.name == "dashboard"
    assert (d / "index.html").is_file()


def test_audio_payload_base64_roundtrip() -> None:
    import base64

    from doda.interfaces.api.server import audio_payload

    payload = audio_payload({"session_id": "s1", "correlation_id": "c1"}, b"MP3-DATA")
    assert payload["session_id"] == "s1"
    assert payload["correlation_id"] == "c1"
    assert base64.b64decode(payload["mp3_b64"]) == b"MP3-DATA"


def test_main_module_importable() -> None:
    import doda.interfaces.api.__main__ as entry

    assert callable(entry.main)
