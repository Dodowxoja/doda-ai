"""``Tool`` porti uchun contract-test bazasi.

Har bir konkret asbob ``make_tool()`` + ``valid_arguments()`` beradi va shu umumiy
tekshiruvlarni meros qilib oladi (nom/tavsif/schema/run natijasi).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from doda.core.interfaces.tool import Tool


class ToolContract:
    """Barcha ``Tool`` implementatsiyalari qanoatlantirishi shart bo'lgan shartlar."""

    def make_tool(self) -> Tool:
        """Sinaladigan asbobni yaratadi (subclass belgilaydi)."""
        raise NotImplementedError

    def valid_arguments(self) -> Mapping[str, Any]:
        """Asbob uchun to'g'ri argumentlar (subclass belgilaydi)."""
        raise NotImplementedError

    def test_has_nonempty_metadata(self) -> None:
        tool = self.make_tool()
        assert tool.name
        assert tool.description

    def test_parameters_is_json_schema(self) -> None:
        params = self.make_tool().parameters
        assert params["type"] == "object"
        assert "properties" in params

    async def test_run_returns_string(self) -> None:
        result = await self.make_tool().run(self.valid_arguments())
        assert isinstance(result, str)
