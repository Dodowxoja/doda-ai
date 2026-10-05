"""``VisionService`` testlari — describe (kadr → LLM Vision) + eventlar."""

from __future__ import annotations

from doda.core.models.event import Event
from doda.core.models.llm import ImageContent, TextContent
from doda.core.models.media import MediaFrame
from doda.perception import VisionService
from doda.providers.bus import AsyncioEventBus
from doda.providers.llm import FakeLLMProvider
from doda.providers.vision import FakeVisionProvider


async def test_describe_returns_llm_text() -> None:
    service = VisionService(
        vision=FakeVisionProvider(),
        llm=FakeLLMProvider(reply="Men stol ko'ryapman"),
        events=AsyncioEventBus(),
    )
    assert await service.describe() == "Men stol ko'ryapman"


async def test_emits_perception_and_result_events() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def on_event(event: Event) -> None:
        seen.append(event.name)

    events.subscribe("perception.frame", on_event)
    events.subscribe("vision.result", on_event)
    service = VisionService(
        vision=FakeVisionProvider(), llm=FakeLLMProvider(reply="ok"), events=events
    )

    await service.describe("nima bu?")
    assert "perception.frame" in seen
    assert "vision.result" in seen


async def test_sends_image_and_question_to_llm() -> None:
    llm = FakeLLMProvider(reply="ok")
    frame = MediaFrame(media_type="image/png", data=b"DATA", source="screen")
    service = VisionService(
        vision=FakeVisionProvider(frame=frame), llm=llm, events=AsyncioEventBus()
    )

    await service.describe("savol")
    content = llm.requests[-1].messages[0].content
    assert any(isinstance(part, ImageContent) for part in content)
    assert any(isinstance(part, TextContent) and part.text == "savol" for part in content)
