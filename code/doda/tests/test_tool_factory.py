"""``build_tool_registry`` testi — standart asboblar to'plami."""

from __future__ import annotations

from pathlib import Path

from code.doda.tools import build_tool_registry


def test_default_toolset(tmp_path: Path) -> None:
    registry = build_tool_registry(workspace=tmp_path)
    names = {spec.name for spec in registry.specs()}
    assert names == {
        "get_current_time",
        "clipboard",
        "send_notification",
        "open",
        "files",
        "run_shell",
    }
