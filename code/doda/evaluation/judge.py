"""``LLMJudge`` — LLM-as-judge baholovchi (sifat mezonlari bo'yicha).

Javobni maqsad/mezon asosida LLM baholaydi va ``{passed, score, reason}`` qaytaradi. Parse
ishlamasa, holat o'tmagan (passed=False, score=0) deb hisoblanadi — sifat testi qat'iy bo'lsin.
"""

from __future__ import annotations

from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.models.evaluation import EvalCase, EvalResult
from code.doda.core.models.llm import LLMRequest, Message, Role
from code.doda.planning.parsing import extract_json_object

_SYSTEM = (
    "Sen sifat-hakamisan. Berilgan savol va javobni bahola va FAQAT JSON obyekt qaytar: "
    '{"passed": true/false, "score": 0..1, "reason": "qisqa izoh"}. Boshqa hech narsa yozma.'
)


class LLMJudge:
    """Javobni LLM orqali sifat mezonlari bo'yicha baholaydi."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def evaluate(self, case: EvalCase, response: str) -> EvalResult:
        request = LLMRequest(
            messages=(Message.text(Role.USER, f"Savol:\n{case.prompt}\n\nJavob:\n{response}"),),
            system=_SYSTEM,
        )
        reply = await self._llm.chat(request)
        parsed = extract_json_object(reply.text)
        if parsed is None or "passed" not in parsed:
            return EvalResult(
                case_id=case.id,
                passed=False,
                score=0.0,
                response=response,
                detail="hakam javobini o'qib bo'lmadi",
            )
        return EvalResult(
            case_id=case.id,
            passed=bool(parsed["passed"]),
            score=float(parsed.get("score", 0.0)),
            response=response,
            detail=str(parsed.get("reason", "")),
        )
