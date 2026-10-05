"""``MemoryManager`` — 7-qatlamli xotira orkestratsiyasi (application qatlami).

Faqat **portlarga** tayanadi (``MemoryStore`` + ``EmbeddingProvider``) — DI orqali beriladi;
konkret implementatsiyani bilmaydi (Clean Architecture). Uch asosiy amal:

- **Remember** — yozuvni embed qilib saqlaydi.
- **Recall** — so'rovni embed qilib, tegishli yozuvlarni topadi (kontekstga inject).
- **Forget** — retention bo'yicha eski yozuvlarni tozalaydi.

**Consolidate** (suhbatdan fakt ajratish) LLM'ni talab qiladi va Agent tsiklida (M4) bajariladi —
bu qatlam faqat saqlash/qidirishning ishonchli poydevorini beradi.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from code.doda.core.interfaces.memory import EmbeddingProvider, MemoryStore
from code.doda.core.interfaces.observability import Observability
from code.doda.core.models.memory import MemoryItem, MemoryType

_PROFILE_TYPES: tuple[MemoryType, ...] = (MemoryType.PREFERENCE,)
_DEFAULT_KEEP: tuple[MemoryType, ...] = (
    MemoryType.PREFERENCE,
    MemoryType.PROJECT,
    MemoryType.PLAN,
)


class MemoryManager:
    """Xotira qatlamlarini boshqaruvchi (remember/recall/profile/forget)."""

    def __init__(
        self,
        store: MemoryStore,
        embedder: EmbeddingProvider,
        observability: Observability | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._obs = observability

    async def remember(
        self,
        content: str,
        type: MemoryType,
        *,
        user_id: str = "owner",
        importance: float = 0.5,
        source: str = "",
    ) -> MemoryItem:
        """Yozuvni embed qilib saqlaydi va qaytaradi."""
        item = MemoryItem.create(
            content, type, user_id=user_id, importance=importance, source=source
        )
        embedding = await self._embedder.embed(content)
        await self._store.add(item, embedding)
        if self._obs is not None:
            self._obs.metric("memory.remember", 1.0, type=type.value)
        return item

    async def recall(
        self,
        query: str,
        k: int = 5,
        *,
        user_id: str | None = None,
        types: Sequence[MemoryType] | None = None,
    ) -> list[MemoryItem]:
        """So'rovga semantik jihatdan tegishli ``k`` ta yozuvni qaytaradi."""
        embedding = await self._embedder.embed(query)
        results = await self._store.search(embedding, k, user_id=user_id, types=types)
        if self._obs is not None:
            self._obs.metric("memory.recall", 1.0)
        return results

    async def profile(self, *, user_id: str = "owner", limit: int = 50) -> list[MemoryItem]:
        """Foydalanuvchi profili (afzalliklar) — persona'ga inject qilish uchun."""
        return await self._store.recent(limit, user_id=user_id, types=_PROFILE_TYPES)

    async def forget(
        self,
        older_than_days: int,
        *,
        keep_types: Sequence[MemoryType] = _DEFAULT_KEEP,
    ) -> int:
        """``older_than_days``dan eski yozuvlarni o'chiradi (``keep_types`` saqlanadi)."""
        cutoff = (datetime.now(UTC) - timedelta(days=older_than_days)).isoformat()
        removed = await self._store.purge_older_than(cutoff, keep_types=keep_types)
        if self._obs is not None:
            self._obs.metric("memory.forget", float(removed))
        return removed
