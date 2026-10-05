"""Multi-Agent testlari — KeywordRouter tanlovi + Orchestrator yo'naltirishi."""

from __future__ import annotations

import pytest

from doda.core.models.event import Event
from doda.orchestrator import KeywordRouter, Orchestrator
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability


class NamedAgent:
    def __init__(self, tag: str) -> None:
        self._tag = tag
        self.handled: list[str] = []

    async def handle(self, user_text: str) -> str:
        self.handled.append(user_text)
        return f"{self._tag}:{user_text}"


# ---------------- KeywordRouter ----------------


async def test_router_default_when_no_keyword() -> None:
    assert await KeywordRouter().route("shunchaki salom") == "main"


async def test_router_matches_coding() -> None:
    assert await KeywordRouter().route("menga python kod yoz") == "coding"


async def test_router_matches_vision() -> None:
    assert await KeywordRouter().route("ekranda nima ko'rinyapti") == "vision"


async def test_router_custom_keywords_and_default() -> None:
    router = KeywordRouter({"music": ("qo'shiq",)}, default="base")
    assert await router.route("qo'shiq qo'y") == "music"
    assert await router.route("boshqa gap") == "base"


# ---------------- Orchestrator ----------------


def test_orchestrator_requires_default_agent() -> None:
    with pytest.raises(ValueError, match="default agent"):
        Orchestrator(
            agents={"coding": NamedAgent("c")}, router=KeywordRouter(), events=AsyncioEventBus()
        )


async def test_routes_to_matching_agent() -> None:
    main = NamedAgent("main")
    coding = NamedAgent("coding")
    orch = Orchestrator(
        agents={"main": main, "coding": coding},
        router=KeywordRouter(),
        events=AsyncioEventBus(),
        observability=BasicObservability(),
    )
    result = await orch.handle("python kod yoz")
    assert result == "coding:python kod yoz"
    assert coding.handled and not main.handled


async def test_falls_back_to_default_when_agent_missing() -> None:
    main = NamedAgent("main")
    # Router "vision" tanlaydi, lekin vision agenti ro'yxatda yo'q → main ishlaydi.
    orch = Orchestrator(agents={"main": main}, router=KeywordRouter(), events=AsyncioEventBus())
    result = await orch.handle("rasmni ko'r")
    assert result == "main:rasmni ko'r"


async def test_emits_routed_event() -> None:
    events = AsyncioEventBus()
    seen: list[dict[str, str]] = []

    async def handler(event: Event) -> None:
        seen.append(dict(event.payload))

    events.subscribe("agent.routed", handler)
    orch = Orchestrator(agents={"main": NamedAgent("main")}, router=KeywordRouter(), events=events)
    await orch.handle("rasmni ko'r")
    assert seen[0] == {"requested": "vision", "resolved": "main"}
