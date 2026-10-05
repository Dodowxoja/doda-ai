"""DODA — enterprise shaxsiy AI Agent platformasi (engine).

Clean Architecture, DI, async, plugin-based. v1.0.0 (flat) yonida quriladi; parity'ga
yetganda almashtiriladi. Public API kirish nuqtasi — :func:`build_container`.
"""

from __future__ import annotations

from doda.config import Settings
from doda.container import Container, build_container

__all__ = ["Container", "Settings", "build_container"]

__version__ = "2.0.0-dev"
