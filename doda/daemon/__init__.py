"""DAEMON qatlami — 24/7 doimiy ishlash supervizori.

``DaemonService`` pluginlarni yuklaydi va fon-siklini (davriy ``scheduler.tick``) yuritadi.
OS-servis o'rnatish (launchd/systemd) — ``packaging/`` mavzusi.
"""

from doda.daemon.service import DaemonService

__all__ = ["DaemonService"]
