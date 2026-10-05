"""Xotira portlari — ``MemoryStore`` (saqlash) va ``EmbeddingProvider`` (vektorlash).

Domen portlari — o'z modulida (M3) birinchi implementatsiya + contract-test bilan.
``MemoryStore`` embedding-agnostik: qidiruv **tayyor vektor** bo'yicha kosinus-o'xshashlik
qiladi; matnni vektorga aylantirish ``EmbeddingProvider`` vazifasi. Shu sabab embedder
almashtirilsa (hashing → sentence-transformers → API), saqlagich o'zgarmaydi.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from code.doda.core.models.memory import MemoryItem, MemoryType


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Matnni vektorga aylantiruvchi (semantik qidiruv uchun)."""

    @property
    def dimension(self) -> int:
        """Vektor o'lchami (barcha vektorlar bir xil o'lchamda)."""
        ...

    async def embed(self, text: str) -> list[float]:
        """Matndan vektor (embedding) qaytaradi."""
        ...


@runtime_checkable
class MemoryStore(Protocol):
    """Xotira yozuvlarini saqlash + vektor bo'yicha qidirish."""

    async def add(self, item: MemoryItem, embedding: Sequence[float]) -> None:
        """Yozuvni (va uning vektorini) saqlaydi."""
        ...

    async def search(
        self,
        embedding: Sequence[float],
        k: int = 5,
        *,
        user_id: str | None = None,
        types: Sequence[MemoryType] | None = None,
    ) -> list[MemoryItem]:
        """Berilgan vektorga eng o'xshash ``k`` ta yozuvni qaytaradi (o'xshashlik bo'yicha)."""
        ...

    async def recent(
        self,
        n: int = 20,
        *,
        user_id: str | None = None,
        types: Sequence[MemoryType] | None = None,
    ) -> list[MemoryItem]:
        """Eng so'nggi ``n`` ta yozuvni qaytaradi (vaqt bo'yicha)."""
        ...

    async def get(self, memory_id: str) -> MemoryItem | None:
        """ID bo'yicha yozuvni qaytaradi yoki ``None``."""
        ...

    async def delete(self, memory_id: str) -> None:
        """Yozuvni soft-delete qiladi (``valid=false``)."""
        ...

    async def purge_older_than(self, cutoff: str, *, keep_types: Sequence[MemoryType] = ()) -> int:
        """``cutoff`` (ISO vaqt)dan eski yozuvlarni o'chiradi (``keep_types`` saqlanadi).

        Qaytaradi: o'chirilgan yozuvlar soni. "Forget" qatlami uchun.
        """
        ...
