"""EVALUATION qatlami — AI sifatini baholash (regressiya + metrikalar).

``EvalRunner`` holatlarni Agentga qarshi yuritadi; ``KeywordEvaluator`` (deterministik) yoki
``LLMJudge`` (LLM-as-judge) baholaydi. Natija ``EvalReport`` (o'tish-foizi, o'rtacha ball).
"""

from doda.evaluation.judge import LLMJudge
from doda.evaluation.runner import EvalRunner
from doda.evaluation.scorer import KeywordEvaluator

__all__ = ["EvalRunner", "KeywordEvaluator", "LLMJudge"]
