"""``PlanningEngine`` testi — reja→bajarish→tekshirish→qayta-rejalash + eventlar."""

from __future__ import annotations

from collections.abc import Sequence

from code.doda.core.models.event import Event
from code.doda.core.models.plan import Plan, PlanStep, Verdict
from code.doda.planning import PlanningEngine
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.observability import BasicObservability


class FakePlanner:
    def __init__(self, descriptions: Sequence[str]) -> None:
        self._descriptions = list(descriptions)
        self.goals: list[str] = []

    async def create_plan(self, goal: str) -> Plan:
        self.goals.append(goal)
        steps = tuple(PlanStep(index=i, description=d) for i, d in enumerate(self._descriptions))
        return Plan(goal=goal, steps=steps)


class FakeAgent:
    def __init__(self) -> None:
        self.handled: list[str] = []

    async def handle(self, user_text: str) -> str:
        self.handled.append(user_text)
        return f"done:{user_text}"


class FakeVerifier:
    def __init__(self, verdicts: Sequence[Verdict]) -> None:
        self._verdicts = list(verdicts)
        self._i = 0

    async def verify(self, goal: str, transcript: str) -> Verdict:
        verdict = self._verdicts[min(self._i, len(self._verdicts) - 1)]
        self._i += 1
        return verdict


async def _collect(bus: AsyncioEventBus, *names: str) -> list[str]:
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    for name in names:
        bus.subscribe(name, handler)
    return seen


async def test_executes_each_step_via_agent() -> None:
    agent = FakeAgent()
    engine = PlanningEngine(
        planner=FakePlanner(["q1", "q2"]),
        executor=agent,
        events=AsyncioEventBus(),
        observability=BasicObservability(),
    )
    result = await engine.run("maqsad")
    assert agent.handled == ["q1", "q2"]
    assert "done:q1" in result
    assert "done:q2" in result


async def test_emits_plan_events_without_verifier() -> None:
    bus = AsyncioEventBus()
    seen = await _collect(
        bus, "plan.created", "plan.step.started", "plan.step.completed", "plan.completed"
    )
    engine = PlanningEngine(planner=FakePlanner(["q1"]), executor=FakeAgent(), events=bus)
    await engine.run("maqsad")
    assert "plan.created" in seen
    assert "plan.step.started" in seen
    assert "plan.step.completed" in seen
    assert "plan.completed" in seen


async def test_verifier_ok_completes_without_replan() -> None:
    planner = FakePlanner(["q1"])
    bus = AsyncioEventBus()
    seen = await _collect(bus, "plan.verified")
    engine = PlanningEngine(
        planner=planner,
        executor=FakeAgent(),
        events=bus,
        verifier=FakeVerifier([Verdict(ok=True, reason="yaxshi")]),
    )
    await engine.run("maqsad")
    assert "plan.verified" in seen
    assert len(planner.goals) == 1  # qayta rejalashtirilmadi


async def test_replans_when_verifier_rejects() -> None:
    planner = FakePlanner(["q1"])
    engine = PlanningEngine(
        planner=planner,
        executor=FakeAgent(),
        events=AsyncioEventBus(),
        verifier=FakeVerifier([Verdict(ok=False, reason="kam"), Verdict(ok=True)]),
        max_replans=1,
    )
    await engine.run("maqsad")
    assert len(planner.goals) == 2  # bir marta qayta rejalashtirildi
    assert "kam" in planner.goals[1]  # feedback keyingi rejaga uzatildi


async def test_replan_is_bounded() -> None:
    planner = FakePlanner(["q1"])
    engine = PlanningEngine(
        planner=planner,
        executor=FakeAgent(),
        events=AsyncioEventBus(),
        verifier=FakeVerifier([Verdict(ok=False, reason="hali kam")]),
        max_replans=2,
    )
    await engine.run("maqsad")
    assert len(planner.goals) == 3  # 1 boshlang'ich + 2 qayta urinish
