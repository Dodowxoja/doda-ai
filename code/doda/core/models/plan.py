"""Rejalashtirish domen modellari — ``Plan`` / ``PlanStep`` / ``Verdict``.

Murakkab so'rov bir nechta bajariladigan qadamga bo'linadi (``Plan``); ``Verifier`` maqsadga
erishilganini baholaydi (``Verdict``). Modellar o'zgarmas (frozen) — domen sof.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PlanStep:
    """Rejadagi bitta bajariladigan qadam."""

    index: int
    description: str


@dataclass(frozen=True, slots=True)
class Plan:
    """Maqsadga erishish uchun tartiblangan qadamlar rejasi."""

    goal: str
    steps: tuple[PlanStep, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class Verdict:
    """Maqsadga erishilganlik hukmi (Verifier natijasi)."""

    ok: bool
    reason: str = ""
