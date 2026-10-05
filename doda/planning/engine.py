"""``PlanningEngine`` — Planner→Executor→Verifier tsiklini boshqaradi.

Murakkab maqsad: reja tuziladi (``Planner``) → har qadam bajariladi (``Agent`` — M4/M6 tool-loop
orqali) → natija baholanadi (``Verifier``, ixtiyoriy) → kerak bo'lsa qayta rejalashtiriladi
(``max_replans`` gacha). Har bosqichda ``plan.*`` eventlari chiqadi (Brain Studio uchun).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from code.doda.core.interfaces.agent import Agent
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.planning import Planner, Verifier
from code.doda.core.models.event import Event
from code.doda.core.models.plan import PlanStep

_SOURCE = "planning"


class PlanningEngine:
    """Maqsadni reja bo'yicha bajaruvchi orkestrator."""

    def __init__(
        self,
        planner: Planner,
        executor: Agent,
        events: EventBus,
        *,
        verifier: Verifier | None = None,
        observability: Observability | None = None,
        max_replans: int = 1,
    ) -> None:
        """Enginni portlar bilan quradi (DI).

        Args:
            planner: Maqsadni qadamlarga bo'luvchi.
            executor: Har bir qadamni bajaruvchi agent (M4 tool-loop).
            events: ``plan.*`` eventlari uchun avtobus.
            verifier: Ixtiyoriy — natijani baholaydi; None bo'lsa tekshirilmaydi.
            observability: Ixtiyoriy — loglash uchun.
            max_replans: Verifier "yetarli emas" desa, qayta urinishlar soni.
        """
        self._planner = planner
        self._executor = executor
        self._events = events
        self._verifier = verifier
        self._obs = observability
        self._max_replans = max_replans

    async def run(self, goal: str) -> str:
        """``goal``ni reja bo'yicha bajaradi va yakuniy natija matnini qaytaradi."""
        trace_id = uuid4().hex
        feedback = ""
        attempt = 0
        while True:
            effective_goal = goal
            if feedback:
                effective_goal = f"{goal}\n\n(Oldingi urinish kamchiligi: {feedback})"
            plan = await self._planner.create_plan(effective_goal)
            await self._emit("plan.created", {"goal": goal, "steps": len(plan.steps)}, trace_id)
            transcript = await self._execute_steps(plan.steps, trace_id)
            if self._verifier is None:
                await self._emit("plan.completed", {"goal": goal}, trace_id)
                return transcript
            verdict = await self._verifier.verify(goal, transcript)
            await self._emit(
                "plan.verified", {"ok": verdict.ok, "reason": verdict.reason}, trace_id
            )
            if verdict.ok or attempt >= self._max_replans:
                await self._emit("plan.completed", {"goal": goal, "ok": verdict.ok}, trace_id)
                return transcript
            feedback = verdict.reason
            attempt += 1

    async def _execute_steps(self, steps: tuple[PlanStep, ...], trace_id: str) -> str:
        """Har bir qadamni agent orqali bajaradi va natijalar transkriptini qaytaradi."""
        lines: list[str] = []
        for step in steps:
            await self._emit(
                "plan.step.started",
                {"index": step.index, "description": step.description},
                trace_id,
            )
            result = await self._executor.handle(step.description)
            await self._emit("plan.step.completed", {"index": step.index}, trace_id)
            lines.append(f"{step.index + 1}. {step.description}\n   → {result}")
        return "\n".join(lines)

    async def _emit(self, name: str, payload: Mapping[str, Any], trace_id: str) -> None:
        await self._events.publish(
            Event(name=name, payload=payload, trace_id=trace_id, source=_SOURCE)
        )
        if self._obs is not None:
            self._obs.log("debug", f"planning event: {name}", **dict(payload))
