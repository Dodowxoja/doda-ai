"""``FeatureFlags`` porti — imkoniyatlarni xavfsiz yoqish/o'chirish (core).

Yangi imkoniyatni kod-shohisiz (deploy'siz) yoqib/o'chirib bo'ladi. Foundation'da oddiy
(config'dan o'qiydigan) implementatsiya; kelajakda masofaviy/foizli rollout — port o'zgarmaydi.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FeatureFlags(Protocol):
    """Imkoniyat bayroqlari (feature flags)."""

    def enabled(self, name: str, *, default: bool = False) -> bool:
        """``name`` bayrog'i yoqilganmi.

        Args:
            name: Bayroq nomi (masalan ``"planning_engine"``).
            default: Bayroq belgilanmagan bo'lsa qaytariladigan qiymat.
        """
        ...
