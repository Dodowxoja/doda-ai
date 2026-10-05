"""LLM domen modellari — provayderdan mustaqil (Claude/Gemini/OpenAI/… uchun umumiy).

Barchasi **o'zgarmas** (frozen). Bu modellar :class:`doda.core.interfaces.llm.LLMProvider`
porti kelishuvini tashkil qiladi — konkret provayder o'z API'sini shu modellarga xaritalaydi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Suhbat xabarining roli."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class TextContent:
    """Matnli kontent bo'lagi."""

    text: str


@dataclass(frozen=True, slots=True)
class ImageContent:
    """Rasm kontenti (vision uchun) — base64 kodlangan."""

    media_type: str  # masalan "image/jpeg"
    data: str  # base64


@dataclass(frozen=True, slots=True)
class ToolResultContent:
    """Bajarilgan tool natijasi (agentdan modelga qaytariladi)."""

    tool_call_id: str
    content: str
    is_error: bool = False


ContentPart = TextContent | ImageContent | ToolResultContent
"""Xabar kontentining bir bo'lagi (matn / rasm / tool-natija)."""


@dataclass(frozen=True, slots=True)
class Message:
    """Suhbatdagi bitta xabar (bir yoki bir nechta kontent bo'lagi)."""

    role: Role
    content: tuple[ContentPart, ...]

    @classmethod
    def text(cls, role: Role, text: str) -> Message:
        """Bitta matnli xabar yaratishning qulay yo'li."""
        return cls(role=role, content=(TextContent(text),))


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Modelga taqdim etiladigan asbob ta'rifi (AI uni chaqira oladi)."""

    name: str
    description: str
    parameters: Mapping[str, Any]  # JSON-schema


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Model chaqirmoqchi bo'lgan asbob (javobda qaytadi)."""

    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Usage:
    """Token sarfi (xarajat/telemetriya uchun)."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True, slots=True)
class Capabilities:
    """Provayder nimani qo'llab-quvvatlaydi (agent shunga moslashadi)."""

    streaming: bool = False
    tools: bool = False
    vision: bool = False


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """LLM'ga so'rov (bitta obyekt — kelajakda maydon qo'shilsa signature o'zgarmaydi)."""

    messages: tuple[Message, ...]
    system: str = ""
    tools: tuple[ToolSpec, ...] = ()
    max_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """LLM javobi (matn + ehtimoliy tool-chaqiruvlar + sarf)."""

    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = field(default_factory=Usage)
    stop_reason: str = ""
    model: str = ""


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """Oqim (stream) javobining bir bo'lagi (matn deltasi)."""

    delta: str
