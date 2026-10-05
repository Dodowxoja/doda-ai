"""``detect_language`` — matn tilini aniqlaydigan yengil evristika (uz default).

O'zbek — asosiy til. Kirill harflari bo'lsa → ruscha; ingliz belgilari ustun bo'lsa → inglizcha;
aks holda → o'zbek (default). Og'ir kutubxonasiz, deterministik. Agent javob tilini shunga
moslashi mumkin (o'zbekcha default, lekin ru/en so'ralsa mos til).
"""

from __future__ import annotations

_RU_RANGE = range(0x0400, 0x0500)  # Kirill alifbosi

_UZ_MARKERS = frozenset(
    {"men", "sen", "bu", "nima", "qanday", "salom", "rahmat", "yordam", "kerak", "uchun"}
)
_EN_MARKERS = frozenset(
    {"the", "what", "how", "hello", "please", "you", "help", "need", "and", "for"}
)


def detect_language(text: str, *, default: str = "uz") -> str:
    """Matn tilini qaytaradi ("ru"/"en"/"uz"); aniqlanmasa ``default``."""
    if any(ord(ch) in _RU_RANGE for ch in text):
        return "ru"
    words = {word.strip(".,!?;:").lower() for word in text.split()}
    uz_hits = len(words & _UZ_MARKERS)
    en_hits = len(words & _EN_MARKERS)
    if en_hits > uz_hits:
        return "en"
    if uz_hits > 0:
        return "uz"
    return default
