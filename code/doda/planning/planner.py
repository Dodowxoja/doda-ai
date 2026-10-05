"""``LLMPlanner`` — LLM yordamida maqsadni qadamlarga bo'ladigan Planner."""

from __future__ import annotations

from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.models.llm import LLMRequest, Message, Role
from code.doda.core.models.plan import Plan, PlanStep
from code.doda.planning.parsing import extract_json_array

_SYSTEM = (
    "Sen rejalashtiruvchisan. Foydalanuvchi maqsadini ketma-ket bajariladigan aniq "
    "qadamlarga bo'l. FAQAT JSON massiv qaytar: qadam matnlari ro'yxati, boshqa hech narsa. "
    "Oddiy maqsad bo'lsa, bitta qadamli massiv qaytar."
)


class LLMPlanner:
    """Maqsadni LLM orqali qadamlar rejasiga aylantiradi."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def create_plan(self, goal: str) -> Plan:
        """``goal``ni qadamlarga bo'ladi; parse ishlamasa, butun maqsad bitta qadam bo'ladi."""
        request = LLMRequest(
            messages=(Message.text(Role.USER, goal),),
            system=_SYSTEM,
        )
        response = await self._llm.chat(request)
        raw = extract_json_array(response.text)
        descriptions = [str(item).strip() for item in raw] if raw else []
        descriptions = [d for d in descriptions if d]
        if not descriptions:
            descriptions = [goal]  # fallback: butun maqsadni bitta qadam sifatida bajaramiz
        steps = tuple(PlanStep(index=i, description=d) for i, d in enumerate(descriptions))
        return Plan(goal=goal, steps=steps)
