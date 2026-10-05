"""``LLMPlanner`` testi — maqsadni qadamlarga bo'lish + fallback."""

from __future__ import annotations

from code.doda.core.models.llm import Role, TextContent
from code.doda.planning import LLMPlanner
from code.doda.providers.llm import FakeLLMProvider


async def test_parses_json_steps() -> None:
    planner = LLMPlanner(FakeLLMProvider(reply='["birinchi", "ikkinchi"]'))
    plan = await planner.create_plan("maqsad")
    assert [s.description for s in plan.steps] == ["birinchi", "ikkinchi"]
    assert [s.index for s in plan.steps] == [0, 1]
    assert plan.goal == "maqsad"


async def test_fallback_to_single_step_when_no_json() -> None:
    planner = LLMPlanner(FakeLLMProvider(reply="oddiy javob, JSON emas"))
    plan = await planner.create_plan("bitta ish")
    assert len(plan.steps) == 1
    assert plan.steps[0].description == "bitta ish"


async def test_empty_array_falls_back() -> None:
    planner = LLMPlanner(FakeLLMProvider(reply="[]"))
    plan = await planner.create_plan("maqsad")
    assert [s.description for s in plan.steps] == ["maqsad"]


async def test_sends_goal_to_llm() -> None:
    llm = FakeLLMProvider(reply='["q"]')
    await LLMPlanner(llm).create_plan("mening maqsadim")
    request = llm.requests[-1]
    assert request.system
    message = request.messages[0]
    assert message.role == Role.USER
    part = message.content[0]
    assert isinstance(part, TextContent)
    assert part.text == "mening maqsadim"
