"""``APIServer`` — delivery qatlami: WebSocket (real-time) + statik dashboard + HTTP API.

``container`` ni oladi va uni tashqi dunyoga ochadi: EventBus → WebSocket (``EventBridge``),
klient buyruqlari → Agent (``CommandRouter``), telemetriya → ``system.metrics`` (``MetricsPump``).
Bir xil portda: ``/ws`` — WebSocket; boshqa yo'llar — statik dashboard va ``/health``·``/status``.

Statik-yo'l hal qilish (``resolve_static``/``serve_path``) sof va test qilinadi; real soket/
tarmoq tsikllari #pragma (``websockets`` lazy import — o'rnatilmagan bo'lsa aniq xabar).
"""

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from doda.container import Container
from doda.interfaces.api.bridge import EventBridge
from doda.interfaces.api.commands import CommandRouter, error_message
from doda.interfaces.api.http_api import health, status
from doda.interfaces.api.metrics import MetricsPump
from doda.interfaces.api.protocol import encode, parse_client_message
from doda.interfaces.api.vision import describe_image, split_data_url
from doda.providers.voice import build_tts

_TEXT_TYPES = ("text/", "application/javascript", "application/json", "image/svg")


def default_static_dir() -> Path:
    """Dashboard statik fayllari papkasi (``interfaces/web/dashboard``)."""
    return Path(__file__).resolve().parent.parent / "web" / "dashboard"


@dataclass(frozen=True, slots=True)
class StaticFile:
    """Uzatiladigan statik fayl (kontent-turi + baytlar)."""

    content_type: str
    body: bytes


def resolve_static(static_dir: Path, url_path: str) -> StaticFile | None:
    """URL yo'lini ``static_dir`` ichidagi faylga xavfsiz hal qiladi (traversal rad etiladi)."""
    rel = url_path.split("?", 1)[0].lstrip("/") or "index.html"
    root = static_dir.resolve()
    target = (root / rel).resolve()
    if target != root and root not in target.parents:
        return None  # papkadan tashqariga chiqishga urinish
    if not target.is_file():
        return None
    ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if any(ctype.startswith(t) for t in _TEXT_TYPES):
        ctype += "; charset=utf-8"
    return StaticFile(ctype, target.read_bytes())


def audio_payload(meta: Mapping[str, str], mp3: bytes) -> dict[str, str]:
    """Audio (mp3 baytlar)ni WS uchun base64 payloadga o'raydi (brauzer ``data:`` bilan chaladi)."""
    return {**meta, "mp3_b64": base64.b64encode(mp3).decode("ascii")}


def serve_path(container: Container, static_dir: Path, path: str) -> tuple[int, str, bytes]:
    """Yo'l uchun HTTP javobini (status, kontent-turi, baytlar) qaytaradi."""
    clean = path.split("?", 1)[0]
    if clean == "/health":
        return 200, "application/json; charset=utf-8", json.dumps(health()).encode()
    if clean == "/status":
        return 200, "application/json; charset=utf-8", json.dumps(status(container)).encode()
    found = resolve_static(static_dir, clean)
    if found is not None:
        return 200, found.content_type, found.body
    return 404, "text/plain; charset=utf-8", b"404 Not Found"


class APIServer:
    """DODA engine'ni WebSocket + HTTP orqali ochuvchi delivery serveri."""

    def __init__(
        self,
        container: Container,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        static_dir: Path | None = None,
        metrics_interval: float = 2.0,
        streaming: bool = True,
    ) -> None:
        self._container = container
        self._host = host
        self._port = port
        self._static_dir = static_dir or default_static_dir()
        self._metrics_interval = metrics_interval
        self.bridge = EventBridge(container.events, observability=container.observability)
        self.commands = CommandRouter(
            container.agent, streaming=streaming, observability=container.observability
        )
        self.metrics = MetricsPump(container.telemetry, self.bridge)
        # TTS (edge-tts, o'zbek) — chat javobini ovozga aylantirib brauzerga yuborish uchun.
        self.tts = build_tts(container.settings.voice, container.secrets)

    @property
    def url(self) -> str:
        """Dashboard ochiladigan HTTP manzili."""
        return f"http://{self._host}:{self._port}/"

    @property
    def ws_url(self) -> str:
        """WebSocket manzili."""
        return f"ws://{self._host}:{self._port}/ws"

    async def run(self) -> None:  # pragma: no cover
        """Serverni ishga tushiradi (statik + HTTP + WebSocket) va cheksiz ishlaydi."""
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("websockets o'rnatilmagan (pip install websockets)") from exc

        self.bridge.start()
        self._container.observability.log("info", f"DODA API server: {self.url}")
        pump = asyncio.create_task(self._metrics_loop())
        # websockets ichki tiplari (ServerConnection/Request) — Any orqali uzatamiz.
        handler: Any = self._ws_handler
        process: Any = self._process_request
        serve = websockets.serve(handler, self._host, self._port, process_request=process)
        try:
            async with serve:
                await asyncio.Future()
        finally:
            pump.cancel()
            self.bridge.stop()

    def _process_request(
        self, connection: object, request: object
    ) -> object | None:  # pragma: no cover
        """Non-WebSocket so'rovlarga HTTP javob beradi; ``/ws`` uchun None (upgrade davom etadi)."""
        from websockets.datastructures import Headers
        from websockets.http11 import Response

        path = str(getattr(request, "path", "/"))
        if path == "/ws":
            return None  # WebSocket handshake'ga o'tsin
        code, ctype, body = serve_path(self._container, self._static_dir, path)
        headers = Headers()
        headers["Content-Type"] = ctype
        headers["Content-Length"] = str(len(body))
        headers["Cache-Control"] = "no-cache"
        reason = {200: "OK", 404: "Not Found"}.get(code, "OK")
        return Response(code, reason, headers, body)

    async def _metrics_loop(self) -> None:  # pragma: no cover
        while True:
            try:
                await self.metrics.pump_once()
            except Exception as exc:
                self._container.observability.log("warning", "metrics pump xato", error=repr(exc))
            await asyncio.sleep(self._metrics_interval)

    async def _ws_handler(self, websocket: object) -> None:  # pragma: no cover
        sink = _WsSink(websocket)
        session_id = uuid4().hex  # har ulanish uchun barqaror sessiya id
        self.bridge.register(sink)
        try:
            await sink.send(encode("session.open", {"session_id": session_id}))
            async for raw in websocket:  # type: ignore[attr-defined]
                message = parse_client_message(raw if isinstance(raw, str) else raw.decode())
                if message is None:
                    continue
                correlation_id = str(message.data.get("correlation_id") or uuid4().hex)
                meta = {"session_id": session_id, "correlation_id": correlation_id}
                await self._dispatch(sink, message, meta)
        except Exception:
            pass
        finally:
            self.bridge.unregister(sink)

    async def _dispatch(  # pragma: no cover
        self, sink: _WsSink, message: object, meta: dict[str, str]
    ) -> None:
        """Xabarni bajaradi — chat streaming/non-stream, kerak bo'lsa javobni ovozga aylantiradi."""
        msg: Any = message
        if msg.type == "vision":  # brauzer kadri → Claude Vision → o'zbekcha tasvir
            await self._vision(sink, msg, meta)
            return
        if msg.type == "speak":  # to'g'ridan-to'g'ri matnni o'qib berish
            await self._speak(sink, str(msg.text), meta)
            return
        speak = bool(msg.data.get("speak")) if hasattr(msg, "data") else False
        if msg.type == "chat" and self.commands.supports_streaming:
            parts: list[str] = []
            async for delta in self.commands.stream(msg):
                parts.append(delta)
                await sink.send(encode("chat.chunk", {**meta, "delta": delta}))
            if parts:
                await sink.send(encode("chat.done", meta))
                if speak:
                    await self._speak(sink, "".join(parts), meta)
            return
        response = await self.commands.handle(msg)
        if response is not None:
            await sink.send(encode("chat.response", {**meta, "text": response}))
            if speak:
                await self._speak(sink, response, meta)

    async def _vision(  # pragma: no cover
        self, sink: _WsSink, message: Any, meta: dict[str, str]
    ) -> None:
        """Brauzer kadrini Claude Vision'ga yuboradi; tasvir ``vision.result`` bo'lib qaytadi."""
        media_type, b64 = split_data_url(str(message.data.get("image_b64", "")))
        if not b64:
            return
        prompt = str(message.data.get("prompt") or "Nima ko'ryapsan?")
        try:
            text = await describe_image(self._container.llm, b64, prompt, media_type=media_type)
        except Exception as exc:
            text = error_message(exc)
        await sink.send(encode("vision.result", {**meta, "text": text}))
        if message.data.get("speak"):
            await self._speak(sink, text, meta)

    async def _speak(
        self, sink: _WsSink, text: str, meta: dict[str, str]
    ) -> None:  # pragma: no cover
        """Matnni edge-tts bilan ovozga aylantirib, brauzerga ``voice.audio`` sifatida yuboradi."""
        clean = text.strip()
        if not clean:
            return
        try:
            mp3 = await self.tts.synthesize(clean)
        except Exception as exc:
            await sink.send(encode("voice.tts_error", {**meta, "error": str(exc)[:120]}))
            return
        await sink.send(encode("voice.audio", audio_payload(meta, mp3)))


class _WsSink:  # pragma: no cover
    """WebSocket ulanishini ``ClientSink`` interfeysiga o'raydi."""

    def __init__(self, websocket: object) -> None:
        self._ws = websocket

    async def send(self, message: str) -> None:
        await self._ws.send(message)  # type: ignore[attr-defined]
