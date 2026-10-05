"""``Settings`` testlari — default, env override, per-OS yo'l."""

from __future__ import annotations

from pathlib import Path

import pytest

from code.doda.config import Settings, default_data_dir


def test_defaults() -> None:
    settings = Settings()
    assert settings.env == "dev"
    assert settings.llm.provider == "claude"
    assert settings.llm.max_tokens == 1024
    assert settings.features == {}


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DODA_ENV", "prod")
    monkeypatch.setenv("DODA_LLM__PROVIDER", "gemini")
    settings = Settings()
    assert settings.env == "prod"
    assert settings.llm.provider == "gemini"


def test_data_dir_is_absolute_path() -> None:
    settings = Settings()
    assert isinstance(settings.paths.data_dir, Path)
    assert settings.paths.data_dir.is_absolute()


def test_data_dir_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("doda.config.sys.platform", "darwin")
    expected = Path.home() / "Library" / "Application Support" / "DODA"
    assert default_data_dir() == expected


def test_data_dir_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("doda.config.sys.platform", "win32")
    monkeypatch.setenv("APPDATA", "/tmp/appdata")
    assert default_data_dir() == Path("/tmp/appdata") / "DODA"


def test_data_dir_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("doda.config.sys.platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/xdg")
    assert default_data_dir() == Path("/tmp/xdg") / "DODA"
