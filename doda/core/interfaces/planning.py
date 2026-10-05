"""Rejalashtirish portlari — ``Planner`` va ``Verifier``.

``Planner`` maqsadni bajariladigan qadamlarga bo'ladi; ``Verifier`` natija maqsadga
mos kelganini baholaydi. Konkret (LLM-asosli) implementatsiyalar ``doda/planning/`` da.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from doda.core.models.plan import Plan, Verdict


@runtime_checkable
class Planner(Protocol):
    """Maqsadni qadamlar rejasiga aylantiradi."""

    async def create_plan(self, goal: str) -> Plan:
        """``goal`` uchun bajariladigan qadamlar rejasini qaytaradi."""
        ...


@runtime_checkable
class Verifier(Protocol):
    """Bajarilgan ish maqsadga erishganini baholaydi."""

    async def verify(self, goal: str, transcript: str) -> Verdict:
        """``transcript`` (bajarilgan qadamlar natijasi) maqsadga mos kelishini baholaydi."""
        ...
