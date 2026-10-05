"""``HashingEmbedding`` testlari."""

from __future__ import annotations

import pytest

from doda.providers.memory import HashingEmbedding


async def test_dimension() -> None:
    embedder = HashingEmbedding(128)
    assert embedder.dimension == 128
    assert len(await embedder.embed("salom")) == 128


async def test_is_deterministic() -> None:
    embedder = HashingEmbedding()
    assert await embedder.embed("salom dunyo") == await embedder.embed("salom dunyo")


async def test_shared_words_are_closer() -> None:
    embedder = HashingEmbedding()
    v1 = await embedder.embed("olma anor")
    v2 = await embedder.embed("olma uzum")  # "olma" umumiy
    v3 = await embedder.embed("kitob daftar")  # umumiy so'z yo'q
    dot_shared = sum(a * b for a, b in zip(v1, v2, strict=True))
    dot_disjoint = sum(a * b for a, b in zip(v1, v3, strict=True))
    assert dot_shared > dot_disjoint


def test_invalid_dimension_raises() -> None:
    with pytest.raises(ValueError):
        HashingEmbedding(0)
