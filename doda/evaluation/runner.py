"""``EvalRunner`` — baholash holatlarini Agentga qarshi yuritib hisobot beradi.

Har bir holat prompti Agentga beriladi, javob ``Evaluator`` bilan baholanadi va natijalar
``EvalReport`` ga jamlanadi (o'tish-foizi, o'rtacha ball). ``eval.completed`` eventi chiqadi.
"""

from __future__ import annotations

from collections.abc import Sequence

from doda.core.interfaces.agent import Agent
from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.evaluation import Evaluator
from doda.core.interfaces.observability import Observability
from doda.core.models.evaluation import EvalCase, EvalReport, EvalResult
from doda.core.models.event import Event

_SOURCE = "evaluation"


class EvalRunner:
    """Baholash to'plamini Agentga qarshi yurituvchi."""

    def __init__(
        self,
        agent: Agent,
        evaluator: Evaluator,
        *,
        events: EventBus | None = None,
        observability: Observability | None = None,
    ) -> None:
        self._agent = agent
        self._evaluator = evaluator
        self._events = events
        self._obs = observability

    async def run(self, cases: Sequence[EvalCase], *, label: str = "") -> EvalReport:
        """Barcha holatlarni bajarib baholaydi va hisobot qaytaradi."""
        results: list[EvalResult] = []
        for case in cases:
            response = await self._agent.handle(case.prompt)
            results.append(await self._evaluator.evaluate(case, response))
        report = EvalReport(results=tuple(results))
        if self._obs is not None:
            self._obs.log(
                "info",
                f"eval tugadi: {label}",
                pass_rate=report.pass_rate,
                mean_score=report.mean_score,
            )
        if self._events is not None:
            await self._events.publish(
                Event(
                    name="eval.completed",
                    payload={"label": label, "pass_rate": report.pass_rate, "total": report.total},
                    source=_SOURCE,
                )
            )
        return report
