"""Wire-protokol — ``Event`` ↔ JSON va engine-eventlarini dashboard-eventlariga tarjima.

Delivery qatlami engine EventBus'idagi ichki eventlarni (``thinking.step``, ``tool.called``…)
frontend kutadigan eventlarga (``agent.thinking``, ``agent.tool_started``, ``module.status``…)
aylantiradi. Bu FE'ni generic saqlaydi: engine nomi o'zgarsa faqat shu tarjima yangilanadi.

XAVFSIZLIK: faqat DODA'ning user-facing narratsiyasi uzatiladi (``thinking.step``) — Claude'ning
xom chain-of-thought'i EMAS.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from code.doda.core.models.event import Event


@dataclass(frozen=True, slots=True)
class ClientMessage:
    """Klientdan (dashboard) kelgan xabar."""

    type: str
    text: str = ""
    data: Mapping[str, Any] = field(default_factory=dict)


def encode(event: str, data: Mapping[str, Any]) -> str:
    """``{event, data}`` ni JSON matnga aylantiradi (JSON-mos bo'lmasa ``str`` bilan)."""
    return json.dumps({"event": event, "data": data}, ensure_ascii=False, default=str)


def parse_client_message(raw: str) -> ClientMessage | None:
    """Klient JSON xabarini ``ClientMessage``ga aylantiradi; buzuq bo'lsa ``None``."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict) or "type" not in obj:
        return None
    return ClientMessage(
        type=str(obj["type"]),
        text=str(obj.get("text", "")),
        data=obj.get("data", {}) if isinstance(obj.get("data"), dict) else {},
    )


def _time(event: Event) -> str:
    return event.timestamp.strftime("%H:%M:%S")


# engine event → (dashboard "module.status" moduli, active/idle)
_MODULE_MAP: dict[str, tuple[str, str]] = {
    "tool.called": ("tools", "active"),
    "tool.result": ("tools", "idle"),
    "perception.frame": ("vision", "active"),
    "vision.result": ("vision", "idle"),
    "plan.created": ("planning", "active"),
    "plan.completed": ("planning", "idle"),
    "task.fired": ("scheduler", "active"),
    "task.completed": ("scheduler", "idle"),
    "voice.speaking": ("voice", "active"),
    "voice.completed": ("voice", "idle"),
    "voice.error": ("voice", "error"),
    "plugin.loaded": ("plugins", "active"),
}


def translate(event: Event) -> list[dict[str, Any]]:
    """Engine eventini frontend uchun bir yoki bir nechta ``{event,data}`` xabarga aylantiradi."""
    messages: list[dict[str, Any]] = []
    p = event.payload
    time = _time(event)

    if event.name == "thinking.step":
        messages.append(
            {
                "event": "agent.thinking",
                "data": {
                    "time": time,
                    "msg": str(p.get("step", "")),
                    "icon": "brain",
                    "tint": "purple",
                },
            }
        )
    elif event.name == "message.created" and p.get("role") == "user":
        messages.append(
            {
                "event": "agent.thinking",
                "data": {
                    "time": time,
                    "msg": "Foydalanuvchi xabari qabul qilindi",
                    "icon": "message-square",
                    "tint": "blue",
                },
            }
        )
    elif event.name == "tool.called":
        messages.append(
            {"event": "agent.tool_started", "data": {"time": time, "name": p.get("name")}}
        )
        messages.append(
            {
                "event": "agent.thinking",
                "data": {
                    "time": time,
                    "msg": f"Asbob ishga tushirildi: {p.get('name', '')}",
                    "icon": "terminal",
                    "tint": "orange",
                },
            }
        )
    elif event.name == "tool.result":
        messages.append(
            {"event": "agent.tool_completed", "data": {"time": time, "name": p.get("name")}}
        )
    elif event.name == "memory.saved":
        messages.append(
            {
                "event": "agent.thinking",
                "data": {"time": time, "msg": "Xotiraga saqlandi", "icon": "save", "tint": "green"},
            }
        )
    else:
        # nomlanmagan eventlar xom ko'rinishda uzatiladi (Brain Studio/debug uchun)
        messages.append(
            {"event": event.name, "data": {**dict(p), "_time": time, "_source": event.source}}
        )

    if event.name in _MODULE_MAP:
        module, status = _MODULE_MAP[event.name]
        messages.append(
            {
                "event": "module.status",
                "data": {
                    "module": module,
                    "status": status,
                    "activity": str(p.get("name", "")) if status == "active" else "—",
                },
            }
        )
    return messages
