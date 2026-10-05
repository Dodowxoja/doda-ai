"""Built-in asboblar testlari — contract + soxta runner bilan buyruq/natija tekshiruvi."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from doda.core.interfaces.tool import Tool
from doda.tests.contracts.tool_contract import ToolContract
from doda.tools import (
    ClipboardTool,
    ClockTool,
    FilesTool,
    NotificationTool,
    OpenTool,
    ShellTool,
)
from doda.tools.runner import CommandResult


def make_runner(
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    capture: dict[str, Any] | None = None,
) -> Any:
    async def runner(command: Sequence[str], stdin_text: str | None) -> CommandResult:
        if capture is not None:
            capture["command"] = list(command)
            capture["stdin"] = stdin_text
        return CommandResult(stdout=stdout, stderr=stderr, returncode=returncode)

    return runner


# ---------------- ClockTool ----------------


class TestClockTool(ToolContract):
    def make_tool(self) -> Tool:
        return ClockTool(now=lambda: datetime(2026, 8, 9, 12, 30, 0))

    def valid_arguments(self) -> Mapping[str, Any]:
        return {}

    async def test_returns_injected_iso_time(self) -> None:
        result = await self.make_tool().run({})
        assert result == "2026-08-09T12:30:00"


# ---------------- ClipboardTool ----------------


class TestClipboardTool(ToolContract):
    def make_tool(self) -> Tool:
        return ClipboardTool(runner=make_runner(stdout="nusxa"))

    def valid_arguments(self) -> Mapping[str, Any]:
        return {"action": "read"}

    async def test_read_returns_clipboard(self) -> None:
        result = await ClipboardTool(runner=make_runner(stdout="matn")).run({"action": "read"})
        assert result == "matn"

    async def test_write_sends_stdin_to_pbcopy(self) -> None:
        captured: dict[str, Any] = {}
        tool = ClipboardTool(runner=make_runner(capture=captured))
        result = await tool.run({"action": "write", "text": "yoz"})
        assert captured["command"] == ["pbcopy"]
        assert captured["stdin"] == "yoz"
        assert "yangilandi" in result

    async def test_unknown_action_raises(self) -> None:
        with pytest.raises(ValueError, match="noma'lum action"):
            await ClipboardTool(runner=make_runner()).run({"action": "xyz"})


# ---------------- NotificationTool ----------------


class TestNotificationTool(ToolContract):
    def make_tool(self) -> Tool:
        return NotificationTool(runner=make_runner())

    def valid_arguments(self) -> Mapping[str, Any]:
        return {"message": "salom"}

    async def test_builds_osascript_command(self) -> None:
        captured: dict[str, Any] = {}
        tool = NotificationTool(runner=make_runner(capture=captured))
        await tool.run({"title": "Sarlavha", "message": "Xabar"})
        assert captured["command"][0] == "osascript"
        assert "Xabar" in captured["command"][-1]
        assert "Sarlavha" in captured["command"][-1]

    async def test_sanitizes_quotes_and_newlines(self) -> None:
        captured: dict[str, Any] = {}
        tool = NotificationTool(runner=make_runner(capture=captured))
        await tool.run({"message": 'a"b\nc'})
        script = captured["command"][-1]
        # Faqat tool qo'shgan 2 juft qo'shtirnoq qolishi kerak (matndagilar tozalangan).
        assert script.count('"') == 4
        assert "\n" not in script

    async def test_failure_raises(self) -> None:
        tool = NotificationTool(runner=make_runner(returncode=1, stderr="rad etildi"))
        with pytest.raises(RuntimeError, match="rad etildi"):
            await tool.run({"message": "x"})


# ---------------- OpenTool ----------------


class TestOpenTool(ToolContract):
    def make_tool(self) -> Tool:
        return OpenTool(runner=make_runner())

    def valid_arguments(self) -> Mapping[str, Any]:
        return {"target": "https://example.com"}

    async def test_full_url_passthrough(self) -> None:
        captured: dict[str, Any] = {}
        out = await OpenTool(runner=make_runner(capture=captured)).run(
            {"target": "https://youtube.com"}
        )
        assert captured["command"] == ["open", "https://youtube.com"]
        assert "Ochildi" in out

    async def test_bare_domain_gets_https(self) -> None:
        captured: dict[str, Any] = {}
        await OpenTool(runner=make_runner(capture=captured)).run({"target": "youtube.com"})
        assert captured["command"] == ["open", "https://youtube.com"]

    async def test_app_name_uses_dash_a(self) -> None:
        captured: dict[str, Any] = {}
        await OpenTool(runner=make_runner(capture=captured)).run({"target": "Calculator"})
        assert captured["command"] == ["open", "-a", "Calculator"]

    async def test_empty_target_raises(self) -> None:
        with pytest.raises(ValueError, match="bo'sh"):
            await OpenTool(runner=make_runner()).run({"target": "  "})

    async def test_failure_reported(self) -> None:
        out = await OpenTool(runner=make_runner(returncode=1, stderr="topilmadi")).run(
            {"target": "Yoqilmagan"}
        )
        assert "ochib bo'lmadi" in out


# ---------------- FilesTool ----------------


class TestFilesTool(ToolContract):
    def make_tool(self) -> Tool:
        return FilesTool(root=Path("/tmp"))

    def valid_arguments(self) -> Mapping[str, Any]:
        return {"action": "list", "path": "."}

    async def test_write_then_read(self, tmp_path: Path) -> None:
        tool = FilesTool(root=tmp_path)
        written = await tool.run({"action": "write", "path": "a.txt", "content": "salom"})
        assert "a.txt" in written
        read = await tool.run({"action": "read", "path": "a.txt"})
        assert read == "salom"

    async def test_list_directory(self, tmp_path: Path) -> None:
        (tmp_path / "b.txt").write_text("x")
        (tmp_path / "a.txt").write_text("y")
        result = await FilesTool(root=tmp_path).run({"action": "list", "path": "."})
        assert result.splitlines() == ["a.txt", "b.txt"]

    async def test_traversal_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="tashqarida"):
            await FilesTool(root=tmp_path).run({"action": "read", "path": "../secret"})

    async def test_read_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="topilmadi"):
            await FilesTool(root=tmp_path).run({"action": "read", "path": "yoq.txt"})

    async def test_list_empty_dir(self, tmp_path: Path) -> None:
        result = await FilesTool(root=tmp_path).run({"action": "list", "path": "."})
        assert result == "(bo'sh papka)"

    async def test_unknown_action_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="noma'lum action"):
            await FilesTool(root=tmp_path).run({"action": "delete", "path": "a"})

    async def test_list_missing_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="topilmadi"):
            await FilesTool(root=tmp_path).run({"action": "list", "path": "yoq"})


# ---------------- ShellTool ----------------


class TestShellTool(ToolContract):
    def make_tool(self) -> Tool:
        return ShellTool(runner=make_runner(stdout="ok"))

    def valid_arguments(self) -> Mapping[str, Any]:
        return {"command": "echo ok"}

    async def test_runs_via_sh(self) -> None:
        captured: dict[str, Any] = {}
        tool = ShellTool(runner=make_runner(stdout="natija", capture=captured))
        result = await tool.run({"command": "ls -la"})
        assert captured["command"] == ["/bin/sh", "-c", "ls -la"]
        assert result == "natija"

    async def test_nonzero_exit_reports_error(self) -> None:
        tool = ShellTool(runner=make_runner(stderr="topilmadi", returncode=127))
        result = await tool.run({"command": "yoq"})
        assert "xato kod 127" in result
        assert "topilmadi" in result

    async def test_empty_command_raises(self) -> None:
        with pytest.raises(ValueError, match="bo'sh buyruq"):
            await ShellTool(runner=make_runner()).run({"command": "   "})

    async def test_empty_stdout_reports_no_output(self) -> None:
        result = await ShellTool(runner=make_runner(stdout="")).run({"command": "true"})
        assert result == "(natija yo'q)"
