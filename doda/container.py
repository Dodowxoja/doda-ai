"""DI Composition Root — barcha kesishuvchi xizmatlarni bitta joyda ulaydi.

Bu yagona joy konkret implementatsiyalarni portlarga bog'laydi (Dependency Injection).
Modullar bir-birini emas, **portni** biladi; ulanish faqat shu yerda. Yangi implementatsiya
almashtirilsa, faqat shu fayl o'zgaradi (SOLID / Dependency Inversion).

Har maydonning turi — **port** (interfeys), qiymati — **implementatsiya**. Shu tayinlash
statik ravishda (mypy) implementatsiya portga mos ekanini kafolatlaydi.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from code.doda.agent import CognitiveAgent, MemoryManager
from code.doda.config import Settings
from code.doda.core.interfaces.agent import Agent
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.flags import FeatureFlags
from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.secrets import SecretStore
from code.doda.daemon import DaemonService
from code.doda.evaluation import EvalRunner, KeywordEvaluator
from code.doda.orchestrator import KeywordRouter, Orchestrator
from code.doda.perception import EnvironmentService, VisionService
from code.doda.planning import LLMPlanner, LLMVerifier, PlanningEngine
from code.doda.plugins import DefaultPluginContext, PluginManager
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.env import ActiveWindowSensor, ClipboardSensor, ClockSensor
from code.doda.providers.flags import SettingsFeatureFlags
from code.doda.providers.llm import build_llm
from code.doda.providers.memory import HashingEmbedding, SQLiteMemoryStore
from code.doda.providers.observability import BasicObservability
from code.doda.providers.scheduler import SQLiteTaskStore
from code.doda.providers.secrets import EnvFileSecretStore
from code.doda.providers.telemetry import PsutilSampler
from code.doda.providers.vision import build_vision_provider
from code.doda.providers.voice import (
    FrameStreamAdapter,
    KeywordWakeDetector,
    build_audio_input,
    build_audio_output,
    build_stt,
    build_tts,
    build_vad,
)
from code.doda.scheduler import Scheduler
from code.doda.telemetry import TelemetryService
from code.doda.tools import ToolRegistry, build_tool_registry
from code.doda.voice import RealtimeVoiceSession, VoicePipeline

_SECRETS_FILENAME = "secrets.json"
_DB_FILENAME = "doda.db"
_TASKS_DB_FILENAME = "tasks.db"
_ANTHROPIC_KEY = "anthropic.key"
_WORKSPACE_DIRNAME = "workspace"


@dataclass(frozen=True, slots=True)
class Container:
    """Ilova uchun tayyor xizmatlar to'plami (portlar bilan tiplangan)."""

    settings: Settings
    observability: Observability
    events: EventBus
    secrets: SecretStore
    flags: FeatureFlags
    llm: LLMProvider
    memory: MemoryManager
    tools: ToolRegistry
    agent: Agent
    vision: VisionService
    environment: EnvironmentService
    planning: PlanningEngine
    voice: VoicePipeline
    realtime_voice: RealtimeVoiceSession
    scheduler: Scheduler
    plugins: PluginManager
    orchestrator: Agent
    daemon: DaemonService
    evaluation: EvalRunner
    telemetry: TelemetryService


def build_container(settings: Settings | None = None) -> Container:
    """Konfiguratsiyaga qarab :class:`Container`ni quradi (kesishuvchi xizmatlarni ulaydi).

    Args:
        settings: Tayyor sozlamalar; berilmasa muhit/``.env``dan yuklanadi.

    Returns:
        Ulangan :class:`Container` (settings, observability, events, secrets, flags).
    """
    settings = settings or Settings()

    logging.getLogger("doda").setLevel(settings.log_level.upper())

    observability_impl = BasicObservability()  # konkret — MetricsReader (snapshot) uchun
    observability: Observability = observability_impl
    events: EventBus = AsyncioEventBus(observability=observability)
    secrets: SecretStore = EnvFileSecretStore(settings.paths.data_dir / _SECRETS_FILENAME)
    flags: FeatureFlags = SettingsFeatureFlags(settings.features)
    llm: LLMProvider = build_llm(
        provider=settings.llm.provider,
        model=settings.llm.model,
        max_tokens=settings.llm.max_tokens,
        api_key=secrets.get(_ANTHROPIC_KEY),
        observability=observability,
    )
    memory = MemoryManager(
        store=SQLiteMemoryStore(settings.paths.data_dir / _DB_FILENAME),
        embedder=HashingEmbedding(),
        observability=observability,
    )
    tools = build_tool_registry(
        workspace=settings.paths.data_dir / _WORKSPACE_DIRNAME,
        observability=observability,
    )
    agent: Agent = CognitiveAgent(
        llm=llm,
        memory=memory,
        events=events,
        observability=observability,
        tools=tools.specs(),
        tool_executor=tools,
    )
    vision = VisionService(
        vision=build_vision_provider(settings.vision.provider),
        llm=llm,
        events=events,
        observability=observability,
    )
    environment = EnvironmentService(
        [ClockSensor(), ClipboardSensor(), ActiveWindowSensor()], events, observability
    )
    planning = PlanningEngine(
        planner=LLMPlanner(llm),
        executor=agent,
        events=events,
        verifier=LLMVerifier(llm),
        observability=observability,
    )
    scheduler = Scheduler(
        store=SQLiteTaskStore(settings.paths.data_dir / _TASKS_DB_FILENAME),
        executor=agent,
        events=events,
        observability=observability,
    )
    voice_cfg = settings.voice
    stt = build_stt(voice_cfg, secrets, observability=observability)
    tts = build_tts(voice_cfg, secrets, observability=observability)
    vad = build_vad(voice_cfg)
    audio_input = build_audio_input(voice_cfg)
    audio_output = build_audio_output(voice_cfg)
    voice = VoicePipeline(
        wake=KeywordWakeDetector(audio_input, stt, keywords=(voice_cfg.wake_word,)),
        audio_input=audio_input,
        stt=stt,
        agent=agent,
        tts=tts,
        audio_output=audio_output,
        events=events,
        observability=observability,
        language=voice_cfg.language,
        record_seconds=voice_cfg.record_seconds,
    )
    realtime_voice = RealtimeVoiceSession(
        audio_stream=FrameStreamAdapter(audio_input),
        vad=vad,
        stt=stt,
        agent=agent,
        tts=tts,
        audio_output=audio_output,
        events=events,
        observability=observability,
        language=voice_cfg.language,
    )
    plugins = PluginManager(
        context=DefaultPluginContext(tools, events),
        events=events,
        observability=observability,
    )
    orchestrator: Agent = Orchestrator(
        agents={"main": agent},
        router=KeywordRouter(),
        events=events,
        observability=observability,
    )
    daemon = DaemonService(
        scheduler=scheduler, plugins=plugins, events=events, observability=observability
    )
    evaluation = EvalRunner(agent, KeywordEvaluator(), events=events, observability=observability)
    telemetry = TelemetryService(
        metrics=observability_impl,
        sampler=PsutilSampler(),
        events=events,
        observability=observability,
    )

    observability.log("info", "DODA container built", env=settings.env)
    return Container(
        settings=settings,
        observability=observability,
        events=events,
        secrets=secrets,
        flags=flags,
        llm=llm,
        memory=memory,
        tools=tools,
        agent=agent,
        vision=vision,
        environment=environment,
        planning=planning,
        voice=voice,
        realtime_voice=realtime_voice,
        scheduler=scheduler,
        plugins=plugins,
        orchestrator=orchestrator,
        daemon=daemon,
        evaluation=evaluation,
        telemetry=telemetry,
    )
