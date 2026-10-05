"""``CognitiveAgent`` — DODA'ning kognitiv yadrosi (Recall → Act → Reflect).

Chatbot emas: har so'rovda xotirani **eslaydi** (recall), persona + kontekst bilan fikrlash
vositasiga (LLM) murojaat qiladi, kerak bo'lsa **asboblarni** ishlatadi (tool-loop), so'ng
muhim narsani xotiraga **saqlaydi** (reflect). Har qadam ``thinking.step`` eventi sifatida
chiqadi (Brain Studio uchun) — bu DODA'ning O'Z narratsiyasi, Claude'ning ichki CoT'i EMAS.

Faqat portlarga/servislarga tayanadi (DI): LLMProvider, MemoryManager, EventBus, ToolExecutor.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any
from uuid import uuid4

from code.doda.agent.conversation import Conversation
from code.doda.agent.memory_manager import MemoryManager
from code.doda.core.interfaces.agent import ToolExecutor
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.interfaces.observability import Observability
from code.doda.core.models.event import Event
from code.doda.core.models.llm import (
    LLMRequest,
    LLMResponse,
    Message,
    Role,
    ToolResultContent,
    ToolSpec,
)
from code.doda.core.models.memory import MemoryType
from code.doda.core.models.persona import Persona

_SOURCE = "agent"


class CognitiveAgent:
    """Recall → Act → Reflect kognitiv tsikli bilan ishlaydigan agent."""

    def __init__(
        self,
        *,
        llm: LLMProvider,
        memory: MemoryManager,
        events: EventBus,
        persona: Persona | None = None,
        conversation: Conversation | None = None,
        tools: Sequence[ToolSpec] = (),
        tool_executor: ToolExecutor | None = None,
        observability: Observability | None = None,
        recall_k: int = 5,
        max_tool_iterations: int = 4,
        remember_episodic: bool = True,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._events = events
        self._persona = persona or Persona()
        self._conversation = conversation or Conversation()
        self._tools = tuple(tools)
        self._tool_executor = tool_executor
        self._obs = observability
        self._recall_k = recall_k
        self._max_tool_iterations = max_tool_iterations
        self._remember_episodic = remember_episodic

    async def handle(self, user_text: str) -> str:
        """Foydalanuvchi matnini to'liq kognitiv tsikl orqali qayta ishlaydi."""
        trace_id = uuid4().hex

        # --- Recall ---
        await self._think("Xotirani izlayapman…", trace_id)
        memories = await self._memory.recall(user_text, k=self._recall_k)
        profile = await self._memory.profile()

        self._conversation.add(Message.text(Role.USER, user_text))
        await self._emit("message.created", {"role": "user", "text": user_text}, trace_id)

        # --- Act ---
        system = self._persona.render(memories, profile)
        await self._think("Fikrlash vositasiga murojaat qilyapman…", trace_id)
        response = await self._act(system, trace_id)

        self._conversation.add(Message.text(Role.ASSISTANT, response.text))
        await self._emit("message.created", {"role": "assistant", "text": response.text}, trace_id)

        # --- Reflect ---
        await self._think("Xotirani yangilayapman…", trace_id)
        await self._reflect(user_text, response.text)
        await self._think("Tayyor.", trace_id)
        return response.text

    async def stream(self, user_text: str) -> AsyncIterator[str]:
        """So'rovni stream rejimida qayta ishlaydi — javob bo'laklari (delta) ketma-ket keladi.

        ``handle`` bilan bir xil kontekst (recall → persona + xotira → Claude → reflect), lekin
        javob to'liq kutilmasdan oqadi. Asbob-loop bu rejimda ishlatilmaydi (real-time chat uchun).
        """
        trace_id = uuid4().hex
        await self._think("Xotirani izlayapman…", trace_id)
        memories = await self._memory.recall(user_text, k=self._recall_k)
        profile = await self._memory.profile()

        self._conversation.add(Message.text(Role.USER, user_text))
        await self._emit("message.created", {"role": "user", "text": user_text}, trace_id)

        system = self._persona.render(memories, profile)
        await self._think("Fikrlash vositasiga murojaat qilyapman…", trace_id)
        parts: list[str] = []
        async for chunk in self._llm.stream(self._build_request(system)):
            parts.append(chunk.delta)
            yield chunk.delta

        text = "".join(parts)
        self._conversation.add(Message.text(Role.ASSISTANT, text))
        await self._emit("message.created", {"role": "assistant", "text": text}, trace_id)
        await self._think("Xotirani yangilayapman…", trace_id)
        await self._reflect(user_text, text)
        await self._think("Tayyor.", trace_id)

    async def _act(self, system: str, trace_id: str) -> LLMResponse:
        """LLM'ga murojaat + tool-loop (asbob so'ralsa, bajarib qayta so'raydi)."""
        response = await self._llm.chat(self._build_request(system))
        iterations = 0
        while (
            response.tool_calls
            and self._tool_executor is not None
            and iterations < self._max_tool_iterations
        ):
            for call in response.tool_calls:
                await self._think(f"Asbobni ishlatyapman: {call.name}", trace_id)
                await self._emit("tool.called", {"name": call.name}, trace_id)
                result = await self._tool_executor.execute(call)
                self._conversation.add(
                    Message(role=Role.TOOL, content=(ToolResultContent(call.id, result),))
                )
                await self._emit("tool.result", {"name": call.name}, trace_id)
            response = await self._llm.chat(self._build_request(system))
            iterations += 1
        return response

    def _build_request(self, system: str) -> LLMRequest:
        return LLMRequest(messages=self._conversation.messages(), system=system, tools=self._tools)

    async def _reflect(self, user_text: str, response_text: str) -> None:
        """Suhbatni episodik xotiraga saqlaydi (consolidation)."""
        if self._remember_episodic:
            await self._memory.remember(
                f"Foydalanuvchi: {user_text} → DODA: {response_text}",
                MemoryType.EPISODIC,
                source="conversation",
            )

    async def _think(self, step: str, trace_id: str) -> None:
        """DODA narratsiyasi — ``thinking.step`` eventi + debug log."""
        if self._obs is not None:
            self._obs.log("debug", f"thinking: {step}", trace_id=trace_id)
        await self._emit("thinking.step", {"step": step}, trace_id)

    async def _emit(self, name: str, payload: Mapping[str, Any], trace_id: str) -> None:
        await self._events.publish(
            Event(name=name, payload=payload, trace_id=trace_id, source=_SOURCE)
        )
