"""DODA modellari ↔ Anthropic (Claude) API formatlari o'rtasidagi SOF xaritalash.

Bu funksiyalar tarmoqsiz, holatsiz va to'liq test qilinadi. Anthropic SDK'ning murakkab
turlariga bog'lanmaslik uchun so'rov ``dict[str, Any]`` sifatida quriladi, javob esa
``Any`` chegarasida (tashqi SDK) xavfsiz ``getattr`` bilan o'qiladi.
"""

from __future__ import annotations

from typing import Any

from doda.core.models.llm import (
    ContentPart,
    ImageContent,
    LLMRequest,
    LLMResponse,
    Role,
    TextContent,
    ToolCall,
    Usage,
)


def _content_block(part: ContentPart) -> dict[str, Any]:
    """Bitta kontent bo'lagini Anthropic kontent-blokiga aylantiradi."""
    if isinstance(part, TextContent):
        return {"type": "text", "text": part.text}
    if isinstance(part, ImageContent):
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": part.media_type, "data": part.data},
        }
    return {
        "type": "tool_result",
        "tool_use_id": part.tool_call_id,
        "content": part.content,
        "is_error": part.is_error,
    }


def _anthropic_role(role: Role) -> str:
    """DODA rolini Anthropic roliga (faqat user/assistant) xaritalaydi."""
    return "assistant" if role is Role.ASSISTANT else "user"


def to_anthropic_params(request: LLMRequest, model: str, default_max_tokens: int) -> dict[str, Any]:
    """:class:`LLMRequest`ni Anthropic ``messages.create`` parametrlariga aylantiradi.

    ``system`` roli Anthropic'da alohida maydon — shu sabab yig'ib, top-level ``system``ga
    qo'yiladi (so'rovdagi ``system`` matni bilan birga).
    """
    system_parts: list[str] = [request.system] if request.system else []
    messages: list[dict[str, Any]] = []
    for message in request.messages:
        if message.role is Role.SYSTEM:
            system_parts.extend(p.text for p in message.content if isinstance(p, TextContent))
            continue
        messages.append(
            {
                "role": _anthropic_role(message.role),
                "content": [_content_block(part) for part in message.content],
            }
        )

    params: dict[str, Any] = {
        "model": model,
        "max_tokens": request.max_tokens or default_max_tokens,
        "messages": messages,
    }
    system = "\n".join(part for part in system_parts if part)
    if system:
        params["system"] = system
    if request.tools:
        params["tools"] = [
            {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
            for t in request.tools
        ]
    return params


def from_anthropic_response(response: Any) -> LLMResponse:
    """Anthropic javob obyektini :class:`LLMResponse`ga aylantiradi (``Any`` chegarasi)."""
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for block in response.content:
        block_type = getattr(block, "type", "")
        if block_type == "text":
            text_parts.append(str(block.text))
        elif block_type == "tool_use":
            arguments = {str(k): v for k, v in dict(block.input).items()}
            tool_calls.append(ToolCall(id=str(block.id), name=str(block.name), arguments=arguments))

    usage_obj = getattr(response, "usage", None)
    usage = Usage(
        input_tokens=int(getattr(usage_obj, "input_tokens", 0) or 0),
        output_tokens=int(getattr(usage_obj, "output_tokens", 0) or 0),
    )
    return LLMResponse(
        text="".join(text_parts),
        tool_calls=tuple(tool_calls),
        usage=usage,
        stop_reason=str(getattr(response, "stop_reason", "") or ""),
        model=str(getattr(response, "model", "") or ""),
    )
