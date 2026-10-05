"""``SettingsFeatureFlags`` testlari."""

from __future__ import annotations

from code.doda.providers.flags import SettingsFeatureFlags


def test_enabled_flag_is_true() -> None:
    flags = SettingsFeatureFlags({"planning": True})
    assert flags.enabled("planning") is True


def test_missing_flag_uses_default() -> None:
    flags = SettingsFeatureFlags({})
    assert flags.enabled("planning") is False
    assert flags.enabled("planning", default=True) is True


def test_explicit_false_overrides_default() -> None:
    flags = SettingsFeatureFlags({"planning": False})
    assert flags.enabled("planning", default=True) is False
