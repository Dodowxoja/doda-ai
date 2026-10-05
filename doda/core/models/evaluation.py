"""AI baholash domen modellari — ``EvalCase`` / ``EvalResult`` / ``EvalReport``.

Regressiya testlari va sifat metrikalari uchun: har bir ``EvalCase`` kirish (prompt) va
kutilgan belgilarni bildiradi; ``Evaluator`` javobni baholab ``EvalResult`` qaytaradi;
``EvalReport`` esa umumiy o'tish-foizi va o'rtacha ballni jamlaydi. Modellar frozen — sof domen.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EvalCase:
    """Bitta baholash holati (kirish + kutilgan belgilar)."""

    id: str
    prompt: str
    expect_contains: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvalResult:
    """Bitta holat bo'yicha baholash natijasi."""

    case_id: str
    passed: bool
    score: float
    response: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class EvalReport:
    """Barcha holatlar bo'yicha jamlangan hisobot."""

    results: tuple[EvalResult, ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        """Holatlar soni."""
        return len(self.results)

    @property
    def passed_count(self) -> int:
        """O'tgan holatlar soni."""
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        """O'tish foizi (0..1); holat bo'lmasa 0."""
        return self.passed_count / self.total if self.total else 0.0

    @property
    def mean_score(self) -> float:
        """O'rtacha ball (0..1); holat bo'lmasa 0."""
        return sum(r.score for r in self.results) / self.total if self.total else 0.0
