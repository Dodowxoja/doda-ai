"""Vision — brauzer kadrini Claude Vision'ga yuborib, o'zbekcha tasvir oladi.

Dashboard kamerasidan kelgan rasm (base64) ``ImageContent`` + savol matni bilan LLM'ga
(Claude, vision-qobiliyatli) yuboriladi. Mavjud LLM pipeline'i ishlatiladi — Claude
integratsiyasi qayta yozilmaydi. Rasm baytlari loglanmaydi.
"""

from __future__ import annotations

from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.models.llm import ImageContent, LLMRequest, Message, Role, TextContent

_VISION_SYSTEM = (
    "Sen DODA'ning ko'zisan. Rasmni diqqat bilan ko'r va O'ZBEK TILIDA qisqa, aniq tasvirla "
    "(nima ko'rinyapti, muhim detallar). Ortiqcha gap yo'q."
)
_DEFAULT_PROMPT = "Nima ko'ryapsan?"


def split_data_url(value: str) -> tuple[str, str]:
    """``data:image/jpeg;base64,XXX`` → ``("image/jpeg","XXX")``; oddiy base64 → jpeg deb qabul."""
    if value.startswith("data:") and "," in value:
        header, b64 = value.split(",", 1)
        media = "image/jpeg"
        if ":" in header and ";" in header:
            media = header.split(":", 1)[1].split(";", 1)[0] or "image/jpeg"
        return media, b64
    return "image/jpeg", value


async def describe_image(
    llm: LLMProvider,
    image_b64: str,
    prompt: str = _DEFAULT_PROMPT,
    *,
    media_type: str = "image/jpeg",
) -> str:
    """Rasmni Claude Vision'ga yuborib, o'zbekcha tasvir matnini qaytaradi."""
    content = (
        ImageContent(media_type=media_type, data=image_b64),
        TextContent(prompt.strip() or _DEFAULT_PROMPT),
    )
    request = LLMRequest(
        messages=(Message(role=Role.USER, content=content),), system=_VISION_SYSTEM
    )
    response = await llm.chat(request)
    return response.text
