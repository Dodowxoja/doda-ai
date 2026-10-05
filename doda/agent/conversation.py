"""``Conversation`` — joriy suhbat konteksti (short-term memory).

Cheklangan oyna: eng so'nggi ``max_messages`` ta xabar saqlanadi (kontekst cheksiz o'smasin).
Bu 7-qatlamli xotiraning **Conversation** qatlami (vaqtinchalik, RAM'da).
"""

from __future__ import annotations

from doda.core.models.llm import Message


class Conversation:
    """Suhbat xabarlarining cheklangan oynasi."""

    def __init__(self, max_messages: int = 20) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages musbat bo'lishi kerak")
        self._max = max_messages
        self._messages: list[Message] = []

    def add(self, message: Message) -> None:
        """Xabar qo'shadi; oyna to'lsa, eng eskisi chiqariladi."""
        self._messages.append(message)
        overflow = len(self._messages) - self._max
        if overflow > 0:
            del self._messages[:overflow]

    def messages(self) -> tuple[Message, ...]:
        """Joriy oynadagi xabarlar (o'zgarmas nusxa)."""
        return tuple(self._messages)

    def clear(self) -> None:
        """Suhbatni tozalaydi."""
        self._messages.clear()
