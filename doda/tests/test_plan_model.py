"""``Plan`` / ``PlanStep`` / ``Verdict`` modellari testi."""

from __future__ import annotations

import dataclasses

import pytest

from doda.core.models.plan import Plan, PlanStep, Verdict


def test_plan_fields() -> None:
    plan = Plan(goal="maqsad", steps=(PlanStep(index=0, description="q1"),))
    assert plan.goal == "maqsad"
    assert plan.steps[0].description == "q1"


def test_plan_default_steps_empty() -> None:
    assert Plan(goal="x").steps == ()


def test_verdict_defaults() -> None:
    assert Verdict(ok=True).reason == ""


def test_models_are_frozen() -> None:
    step = PlanStep(index=0, description="q")
    with pytest.raises(dataclasses.FrozenInstanceError):
        step.index = 1  # type: ignore[misc]
