"""``CognitiveAgent`` testlari — Recall → Act → Reflect, eventlar, tool-loop."""

from __future__ import annotations

from pathlib import Path

from code.doda.agent import CognitiveAgent, MemoryManager
from code.doda.core.interfaces.agent import ToolExecutor
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.models.event import Event
from code.doda.core.models.llm import LLMResponse, ToolCall, ToolSpec
from code.doda.core.models.memory import MemoryType
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.llm import FakeLLMProvider
from code.doda.providers.memory import HashingEmbedding, SQLiteMemoryStore
from code.doda.providers.observability import BasicObservability


def _memory(tmp_path: Path) -> MemoryManager:
    return MemoryManager(SQLiteMemoryStore(tmp_path / "memory.db"), HashingEmbedding())


def _agent(
    tmp_path: Path,
    *,
    llm: FakeLLMProvider,
    events: EventBus | None = None,
    memory: MemoryManager | None = None,
    tools: tuple[ToolSpec, ...] = (),
    executor: ToolExecutor | None = None,
    observability: BasicObservability | None = None,
) -> CognitiveAgent:
    return CognitiveAgent(
        llm=llm,
        memory=memory or _memory(tmp_path),
        events=events or AsyncioEventBus(),
        tools=tools,
        tool_executor=executor,
        observability=observability,
    )


async def test_returns_llm_response(tmp_path: Path) -> None:
    agent = _agent(tmp_path, llm=FakeLLMProvider(reply="Salom!"))
    assert await agent.handle("hi") == "Salom!"


async def test_stream_yields_deltas_and_reflects(tmp_path: Path) -> None:
    events = AsyncioEventBus()
    roles: list[str] = []

    async def on_message(event: Event) -> None:
        roles.append(str(event.payload["role"]))

    events.subscribe("message.created", on_message)
    memory = _memory(tmp_path)
    agent = _agent(
        tmp_path,
        llm=FakeLLMProvider(reply="salom dunyo"),
        events=events,
        memory=memory,
        observability=BasicObservability(),
    )

    deltas = [delta async for delta in agent.stream("hi")]
    assert "".join(deltas).strip() == "salom dunyo"
    assert roles == ["user", "assistant"]  # oqim yakunida to'liq xabar chiqadi

    recalled = await memory.recall("salom", k=5)
    assert any("DODA: salom dunyo" in item.content for item in recalled)  # episodik saqlandi


async def test_emits_thinking_and_message_events(tmp_path: Path) -> None:
    events = AsyncioEventBus()
    steps: list[str] = []
    roles: list[str] = []

    async def on_think(event: Event) -> None:
        steps.append(str(event.payload["step"]))

    async def on_message(event: Event) -> None:
        roles.append(str(event.payload["role"]))

    events.subscribe("thinking.step", on_think)
    events.subscribe("message.created", on_message)
    agent = _agent(tmp_path, llm=FakeLLMProvider(reply="ok"), events=events)

    await agent.handle("salom")
    assert len(steps) >= 3
    assert roles == ["user", "assistant"]


async def test_reflect_saves_episodic_memory(tmp_path: Path) -> None:
    memory = _memory(tmp_path)
    agent = _agent(tmp_path, llm=FakeLLMProvider(reply="javob"), memory=memory)
    await agent.handle("mening ismim Ali")
    episodic = await memory.recall("Ali", k=5, types=[MemoryType.EPISODIC])
    assert len(episodic) >= 1


async def test_recall_injects_memory_into_system_prompt(tmp_path: Path) -> None:
    memory = _memory(tmp_path)
    llm = FakeLLMProvider(reply="ok")
    agent = _agent(tmp_path, llm=llm, memory=memory)
    await memory.remember("Foydalanuvchi Flutter yoqtiradi", MemoryType.PREFERENCE)
    await agent.handle("Flutter haqida gapir")
    assert "Flutter" in llm.requests[-1].system


async def test_tool_loop_executes_tools(tmp_path: Path) -> None:
    llm = FakeLLMProvider(
        responses=[
            LLMResponse(text="", tool_calls=(ToolCall("c1", "calc", {"x": 1}),)),
            LLMResponse(text="Javob: 2"),
        ]
    )

    class _Executor:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def execute(self, call: ToolCall) -> str:
            self.calls.append(call.name)
            return "2"

    executor = _Executor()
    tools = (ToolSpec("calc", "hisoblaydi", {"type": "object"}),)
    agent = _agent(tmp_path, llm=llm, tools=tools, executor=executor)

    result = await agent.handle("2 ni hisobla")
    assert result == "Javob: 2"
    assert executor.calls == ["calc"]
