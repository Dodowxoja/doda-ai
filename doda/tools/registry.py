"""``ToolRegistry`` — asboblarni jamlab, ``ToolExecutor`` sifatida tsiklga ulaydi.

Agent (M4) tool-chaqiruvni ``execute(ToolCall)`` orqali bajaradi; LLM'ga esa ``specs()``
ro'yxatini beradi. Registr nomni asbobga xaritalab yuboradi, xatolarni izolyatsiya qiladi
(bitta asbob xatosi tsiklni buzmasin — LLM'ga xato-matn qaytadi).
"""

from __future__ import annotations

from collections.abc import Iterable

from doda.core.interfaces.observability import Observability
from doda.core.interfaces.tool import Tool
from doda.core.models.llm import ToolCall, ToolSpec


def tool_spec(tool: Tool) -> ToolSpec:
    """``Tool`` portidan LLM uchun ``ToolSpec`` yasaydi."""
    return ToolSpec(name=tool.name, description=tool.description, parameters=tool.parameters)


class ToolRegistry:
    """Asboblar registri; ``ToolExecutor`` portini bajaradi."""

    def __init__(
        self,
        tools: Iterable[Tool] = (),
        observability: Observability | None = None,
    ) -> None:
        """Registrni asboblar bilan quradi.

        Args:
            tools: Boshlang'ich asboblar; nomi noyob bo'lishi shart.
            observability: Ixtiyoriy — asbob xatolarini loglash uchun.

        Raises:
            ValueError: Ikki asbob bir xil nomga ega bo'lsa.
        """
        self._tools: dict[str, Tool] = {}
        self._obs = observability
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        """Asbobni qo'shadi (nomi bo'yicha).

        Raises:
            ValueError: Shu nomli asbob allaqachon mavjud.
        """
        if tool.name in self._tools:
            raise ValueError(f"Asbob '{tool.name}' allaqachon ro'yxatdan o'tgan")
        self._tools[tool.name] = tool

    def specs(self) -> tuple[ToolSpec, ...]:
        """Barcha asboblarning LLM-spetsifikatsiyalari."""
        return tuple(tool_spec(tool) for tool in self._tools.values())

    async def execute(self, call: ToolCall) -> str:
        """``call`` asbobini bajaradi; noma'lum yoki xato holatda xato-matn qaytadi."""
        tool = self._tools.get(call.name)
        if tool is None:
            return f"(xato: noma'lum asbob '{call.name}')"
        try:
            return await tool.run(call.arguments)
        except Exception as exc:  # asbob xatosi tsiklni buzmasin — LLM'ga xabar beramiz
            if self._obs is not None:
                self._obs.log("warning", f"asbob '{call.name}' xato berdi", error=repr(exc))
            return f"(xato: {exc})"
