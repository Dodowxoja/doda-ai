"""``SettingsFeatureFlags`` — FeatureFlags portining config asosidagi implementatsiyasi.

Bayroq qiymatlarini :class:`doda.config.Settings` ning ``features`` lug'atidan o'qiydi.
Oddiy va yetarli; kelajakda masofaviy/foizli rollout shu portni almashtiradi.
"""

from __future__ import annotations

from collections.abc import Mapping


class SettingsFeatureFlags:
    """Config ``features`` lug'atidan o'qiydigan feature-flag manbai."""

    def __init__(self, flags: Mapping[str, bool]) -> None:
        """
        Args:
            flags: Bayroq nomi → yoqilgan/o'chirilgan lug'ati (``Settings.features``).
        """
        self._flags = dict(flags)

    def enabled(self, name: str, *, default: bool = False) -> bool:
        """Bayroq yoqilganmi; belgilanmagan bo'lsa ``default``."""
        return self._flags.get(name, default)
