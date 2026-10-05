"""API/delivery qatlami — WebSocket + HTTP orqali engine'ni dashboardga ochadi.

``APIServer(container).run()`` — EventBus'ni real-time WebSocket'ga ulaydi, klient buyruqlarini
Agentga yo'naltiradi, telemetriyani uzatadi. ``python -m doda.interfaces.api`` bilan ishga tushadi.
"""

from doda.interfaces.api.bridge import EVENT_CATALOG, ClientSink, EventBridge
from doda.interfaces.api.commands import CommandRouter
from doda.interfaces.api.metrics import MetricsPump
from doda.interfaces.api.protocol import ClientMessage, encode, parse_client_message, translate
from doda.interfaces.api.server import APIServer, default_static_dir

__all__ = [
    "EVENT_CATALOG",
    "APIServer",
    "ClientMessage",
    "ClientSink",
    "CommandRouter",
    "EventBridge",
    "MetricsPump",
    "default_static_dir",
    "encode",
    "parse_client_message",
    "translate",
]
