"""ORCHESTRATOR qatlami — Multi-Agent yo'naltirish (so'rov → mos agent).

``Orchestrator`` ``Agent`` portini bajaradi va so'rovni ``AgentRouter`` yordamida tegishli
agentga uzatadi. v1.0 da bitta "main" agent; yangi agentlar interfeys orqali qo'shiladi.
"""

from doda.orchestrator.orchestrator import Orchestrator
from doda.orchestrator.router import KeywordRouter

__all__ = ["KeywordRouter", "Orchestrator"]
