"""PORTLAR (abstraksiyalar/Protocol) — DODA yadrosi kelishuvlari.

Foundation (Modul 1) shu KESISHUVCHI portlarni belgilaydi: :class:`EventBus`,
:class:`Observability`, :class:`SecretStore`, :class:`FeatureFlags`.

DOMEN portlari (LLMProvider, MemoryStore, VisionProvider, Tool, Plugin, Scheduler,
Planner, Agent) o'z modullarida (M2, M3, …) belgilanadi — interfeys aynan kerak bo'lganda,
barqaror shaklda (YAGNI + "public API stable"). Qarang: ``doda/README.md``.
"""

from __future__ import annotations

from code.doda.core.interfaces.agent import Agent, ToolExecutor
from code.doda.core.interfaces.bus import EventBus, EventHandler, Subscription
from code.doda.core.interfaces.flags import FeatureFlags
from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.interfaces.memory import EmbeddingProvider, MemoryStore
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.perception import EnvSensor, VisionProvider
from code.doda.core.interfaces.secrets import SecretStore

__all__ = [
    "Agent",
    "EmbeddingProvider",
    "EnvSensor",
    "EventBus",
    "EventHandler",
    "FeatureFlags",
    "LLMProvider",
    "MemoryStore",
    "Observability",
    "SecretStore",
    "Subscription",
    "ToolExecutor",
    "VisionProvider",
]
