"""``Orchestrator`` — so'rovni mos agentga yo'naltiradi (``Agent`` portini bajaradi).

Router agent nomini beradi; Orchestrator shu agentni topib ishlatadi. Nom topilmasa
``default`` agent ishlaydi (xavfsiz fallback). ``agent.routed`` eventi chiqadi (Brain Studio).
v1.0 da faqat "main" ro'yxatda — yangi agent (Coding/Vision...) qo'shilsa avtomatik ishlaydi.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from code.doda.core.interfaces.agent import Agent
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.orchestrator import AgentRouter
from code.doda.core.models.event import Event

_SOURCE = "orchestrator"


class Orchestrator:
    """Bir nechta agentni boshqarib, so'rovni mosiga yo'naltiruvchi agent."""

    def __init__(
        self,
        agents: Mapping[str, Agent],
        router: AgentRouter,
        events: EventBus,
        *,
        default: str = "main",
        observability: Observability | None = None,
    ) -> None:
        """Orkestartorni agentlar to'plami va router bilan quradi.

        Args:
            agents: Nom→agent xaritasi (``default`` nomli agent bo'lishi shart).
            router: So'rovni agent nomiga aylantiruvchi.
            events: ``agent.routed`` eventi uchun avtobus.
            default: Router nomi topilmasa ishlatiladigan agent nomi.
            observability: Ixtiyoriy — loglash uchun.

        Raises:
            ValueError: ``default`` nomli agent ``agents`` ichida bo'lmasa.
        """
        if default not in agents:
            raise ValueError(f"default agent '{default}' agents ichida yo'q")
        self._agents = dict(agents)
        self._router = router
        self._events = events
        self._default = default
        self._obs = observability

    async def handle(self, user_text: str) -> str:
        """So'rovni mos agentga yo'naltirib, javobini qaytaradi."""
        trace_id = uuid4().hex
        requested = await self._router.route(user_text)
        resolved = requested if requested in self._agents else self._default
        await self._events.publish(
            Event(
                name="agent.routed",
                payload={"requested": requested, "resolved": resolved},
                trace_id=trace_id,
                source=_SOURCE,
            )
        )
        if self._obs is not None:
            self._obs.log("debug", f"routed to '{resolved}'", requested=requested)
        return await self._agents[resolved].handle(user_text)
