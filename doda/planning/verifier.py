"""``LLMVerifier`` — LLM yordamida maqsadga erishilganini baholaydigan Verifier."""

from __future__ import annotations

from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.models.llm import LLMRequest, Message, Role
from code.doda.core.models.plan import Verdict
from code.doda.planning.parsing import extract_json_object

_SYSTEM = (
    "Sen sifat-nazoratchisisan. Maqsad va bajarilgan ish natijasini solishtir. FAQAT JSON "
    'obyekt qaytar: {"ok": true/false, "reason": "qisqa izoh"}. Boshqa hech narsa yozma.'
)


class LLMVerifier:
    """Bajarilgan ish maqsadga mos kelishini LLM orqali baholaydi."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def verify(self, goal: str, transcript: str) -> Verdict:
        """Natijani baholaydi; parse ishlamasa, bloklamaslik uchun ``ok=True`` qaytadi."""
        request = LLMRequest(
            messages=(Message.text(Role.USER, f"Maqsad:\n{goal}\n\nNatija:\n{transcript}"),),
            system=_SYSTEM,
        )
        response = await self._llm.chat(request)
        parsed = extract_json_object(response.text)
        if parsed is None or "ok" not in parsed:
            return Verdict(ok=True, reason="tekshiruv aniq emas (fail-open)")
        return Verdict(ok=bool(parsed["ok"]), reason=str(parsed.get("reason", "")))
