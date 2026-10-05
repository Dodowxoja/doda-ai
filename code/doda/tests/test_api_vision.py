"""Vision delivery testi — ``split_data_url`` + ``describe_image`` (tarmoqsiz, FakeLLM)."""

from __future__ import annotations

from code.doda.core.models.llm import ImageContent, TextContent
from code.doda.interfaces.api.vision import describe_image, split_data_url
from code.doda.providers.llm import FakeLLMProvider


def test_split_data_url_jpeg() -> None:
    media, b64 = split_data_url("data:image/jpeg;base64,QUJD")
    assert media == "image/jpeg"
    assert b64 == "QUJD"


def test_split_data_url_png() -> None:
    media, b64 = split_data_url("data:image/png;base64,WFla")
    assert media == "image/png"
    assert b64 == "WFla"


def test_split_data_url_plain_base64() -> None:
    assert split_data_url("QUJD") == ("image/jpeg", "QUJD")


async def test_describe_returns_llm_text() -> None:
    llm = FakeLLMProvider(reply="Men stol va noutbuk ko'ryapman")
    result = await describe_image(llm, "QUJD", "Nima bu?", media_type="image/png")
    assert result == "Men stol va noutbuk ko'ryapman"


async def test_describe_sends_image_and_prompt() -> None:
    llm = FakeLLMProvider(reply="ok")
    await describe_image(llm, "QUJD", "savol")
    content = llm.requests[-1].messages[0].content
    image = next(p for p in content if isinstance(p, ImageContent))
    assert image.data == "QUJD"
    assert image.media_type == "image/jpeg"
    assert any(isinstance(p, TextContent) and p.text == "savol" for p in content)
    assert llm.requests[-1].system  # vision system-prompt bor


async def test_describe_empty_prompt_defaults() -> None:
    llm = FakeLLMProvider(reply="ok")
    await describe_image(llm, "QUJD", "   ")
    content = llm.requests[-1].messages[0].content
    assert any(isinstance(p, TextContent) and "ko'ryapsan" in p.text for p in content)
