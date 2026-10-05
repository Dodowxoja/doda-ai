"""TOOL modullari: registry + built-in asboblar (vaqt/clipboard/bildirishnoma/fayl/shell).

``ToolRegistry`` asboblarni ``ToolExecutor`` sifatida jamlaydi va Agent (M4) tsikliga ulanadi.
Yangi asbob = ``Tool`` portining yangi implementatsiyasi (core o'zgarmaydi).
"""

from code.doda.tools.clipboard_tool import ClipboardTool
from code.doda.tools.clock_tool import ClockTool
from code.doda.tools.factory import build_tool_registry
from code.doda.tools.files_tool import FilesTool
from code.doda.tools.notification_tool import NotificationTool
from code.doda.tools.open_tool import OpenTool
from code.doda.tools.registry import ToolRegistry, tool_spec
from code.doda.tools.runner import CommandResult, CommandRunner, subprocess_run
from code.doda.tools.shell_tool import ShellTool

__all__ = [
    "ClipboardTool",
    "ClockTool",
    "CommandResult",
    "CommandRunner",
    "FilesTool",
    "NotificationTool",
    "OpenTool",
    "ShellTool",
    "ToolRegistry",
    "build_tool_registry",
    "subprocess_run",
    "tool_spec",
]
