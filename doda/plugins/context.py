"""``DefaultPluginContext`` — pluginlarni asbob-registri va hodisa-avtobusiga ulaydi.

Plugin faqat shu cheklangan konteks orqali ishlaydi (yadroga to'g'ridan-to'g'ri kira olmaydi).
Obunalar yozib boriladi — teardown paytida hammasini bekor qilish uchun.
"""

from __future__ import annotations

from doda.core.interfaces.bus import EventBus, EventHandler, Subscription
from doda.core.interfaces.tool import Tool
from doda.tools import ToolRegistry


class DefaultPluginContext:
    """Plugin ro'yxatga olish uchun standart konteks (ToolRegistry + EventBus)."""

    def __init__(self, tools: ToolRegistry, events: EventBus) -> None:
        self._tools = tools
        self._events = events
        self.subscriptions: list[Subscription] = []

    def register_tool(self, tool: Tool) -> None:
        self._tools.register(tool)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        self.subscriptions.append(self._events.subscribe(event, handler))
