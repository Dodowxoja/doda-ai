"""``HashingEmbedding`` — bog'liqliksiz (torch'siz) leksik embedding (feature hashing).

Har token belgilangan o'lchamli vektorning bitta o'lchamiga xeshlanadi va sanaladi.
Deterministik, tez, tashqi kutubxonasiz — Foundation/vertical-slice uchun yetarli.

**Eslatma:** bu **leksik** (so'z-darajasidagi) o'xshashlik, chuqur **semantik** emas.
Haqiqiy semantik embedding (sentence-transformers / API) ``EmbeddingProvider`` porti ortida
keyinroq ulanadi — ``MemoryStore`` va ``MemoryManager`` o'zgarmaydi.
"""

from __future__ import annotations

import hashlib
import re

_TOKEN_RE = re.compile(r"\w+")


class HashingEmbedding:
    """Feature-hashing asosidagi leksik embedding."""

    def __init__(self, dimension: int = 256) -> None:
        if dimension <= 0:
            raise ValueError("dimension musbat bo'lishi kerak")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """Matndan hisoblagich-vektor (feature hashing) qaytaradi."""
        vector = [0.0] * self._dimension
        for token in _TOKEN_RE.findall(text.lower()):
            vector[self._bucket(token)] += 1.0
        return vector

    def _bucket(self, token: str) -> int:
        """Tokenni vektor o'lchamiga (deterministik) xeshlaydi."""
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
        return int.from_bytes(digest, "big") % self._dimension
