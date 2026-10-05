"""HTTP handlerlar (sof funksiyalar) — ``/health``, ``/status``, ``/api/v1/chat``.

Transportdan mustaqil: har handler oddiy dict qaytaradi (server JSON qiladi). Shu bois to'liq
test qilinadi (soxta container bilan). To'liq ``/api/v1`` yuzasi ``docs/API.md`` da; bu yerda
dashboard uchun zarur minimal to'plam.
"""

from __future__ import annotations

from typing import Any

from code.doda.container import Container
from code.doda.core.interfaces.agent import Agent

_VERSION = "2.0.0-dev"


def health() -> dict[str, Any]:
    """Servis tirikligini bildiradi."""
    return {"status": "ok", "service": "doda", "version": _VERSION}


def status(container: Container) -> dict[str, Any]:
    """Engine holati — muhit, provayder, komponentlar."""
    return {
        "service": "doda",
        "version": _VERSION,
        "env": container.settings.env,
        "llm_provider": container.settings.llm.provider,
        "model": container.settings.llm.model,
        "components": {
            "agent": "ready",
            "memory": "ready",
            "voice": "ready" if container.settings.voice.enable_voice else "disabled",
            "vision": "ready",
            "scheduler": "ready",
            "plugins": container.plugins.names(),
        },
    }


async def chat(agent: Agent, body: dict[str, Any]) -> dict[str, Any]:
    """Agentga matn beradi va javob qaytaradi (chat = voice bilan bir xil pipeline)."""
    text = str(body.get("message") or body.get("text") or "").strip()
    if not text:
        return {"error": "bo'sh xabar: 'message' yoki 'text' talab qilinadi"}
    response = await agent.handle(text)
    return {"response": response}
