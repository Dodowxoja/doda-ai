"""``build_tool_registry`` — DODA'ning standart asboblar to'plamini quradi.

v1.0 built-in asboblar: vaqt / clipboard / bildirishnoma / fayllar (root bilan cheklangan) /
shell. Browser / Calendar / Weather kabi tarmoq-OS integratsiyalari v1.1 ga qoldirildi
(``VERSION_PLAN``) — port barqaror, ular keyin yangi adapter sifatida qo'shiladi.
"""

from __future__ import annotations

from pathlib import Path

from doda.core.interfaces.observability import Observability
from doda.tools.clipboard_tool import ClipboardTool
from doda.tools.clock_tool import ClockTool
from doda.tools.files_tool import FilesTool
from doda.tools.notification_tool import NotificationTool
from doda.tools.open_tool import OpenTool
from doda.tools.registry import ToolRegistry
from doda.tools.shell_tool import ShellTool


def build_tool_registry(
    workspace: Path, observability: Observability | None = None
) -> ToolRegistry:
    """Standart built-in asboblar bilan ``ToolRegistry`` quradi.

    Args:
        workspace: ``FilesTool`` cheklanadigan ish-papka (barcha fayl amallari shu ichida).
        observability: Ixtiyoriy — asbob xatolarini loglash uchun.
    """
    return ToolRegistry(
        [
            ClockTool(),
            ClipboardTool(),
            NotificationTool(),
            OpenTool(),
            FilesTool(root=workspace),
            ShellTool(),
        ],
        observability=observability,
    )
