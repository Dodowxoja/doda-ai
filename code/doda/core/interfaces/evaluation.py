"""``Evaluator`` porti — AI javobini baholash (rule-based yoki LLM-as-judge).

``EvalRunner`` (M13) har bir holat javobini shu port orqali baholaydi. Konkret baholovchilar
(kalit-so'z yoki LLM-hakam) ``doda/evaluation/`` da; port ikkalasini ham qamrab oladi.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from code.doda.core.models.evaluation import EvalCase, EvalResult


@runtime_checkable
class Evaluator(Protocol):
    """Holat javobini baholab natija qaytaradi."""

    async def evaluate(self, case: EvalCase, response: str) -> EvalResult:
        """``case`` uchun ``response`` javobini baholaydi."""
        ...
