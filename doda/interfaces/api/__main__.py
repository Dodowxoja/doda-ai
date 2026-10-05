"""``python -m doda.interfaces.api`` — DODA delivery serverini ishga tushiradi.

Bitta buyruq bilan hammasi: statik dashboard + HTTP API + real-time WebSocket. So'ng brauzerda
ko'rsatilgan manzilni oching.
"""

from __future__ import annotations

import asyncio

from doda.container import build_container
from doda.interfaces.api.server import APIServer


def main() -> None:  # pragma: no cover
    """Container quradi va API serverni ishga tushiradi (Ctrl+C bilan to'xtaydi)."""
    container = build_container()
    # Non-streaming: chat/voice tool-loop'dan o'tadi — DODA amallarni bajaradi (open, shell...).
    server = APIServer(container, streaming=False)
    print("\n  \U0001f9e0  DODA — AI Agent OS")
    print(f"     Dashboard:  {server.url}")
    print(f"     WebSocket:  {server.ws_url}")
    print("     To'xtatish: Ctrl+C\n")
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        container.observability.log("info", "DODA API server to'xtatildi")


if __name__ == "__main__":  # pragma: no cover
    main()
