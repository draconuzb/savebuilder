"""Premium (custom) emoji yordamchisi.

Foydalanish:
    text, entities = build_premium_text([
        ("rocket", " SaveBuilder"),   # premium emoji + oddiy matn
    ])
    await message.answer(text, entities=entities)

CUSTOM_EMOJI lug'atiga premium akkauntdan olingan custom_emoji_id larni yozing.
ID yo'q bo'lsa — fallback unicode emoji ishlatiladi (bot baribir ishlaydi)."""
from __future__ import annotations

from aiogram.types import MessageEntity

# nom -> (fallback_unicode, custom_emoji_id | None)
# custom_emoji_id larни premium akkauntdan oling (masalan @RawDataBot orqali entity ko'rib).
CUSTOM_EMOJI: dict[str, tuple[str, str | None]] = {
    "robot": ("🤖", None),
    "rocket": ("⚡️", None),
    "fire": ("🔥", None),
    "check": ("✅", None),
    "money": ("💳", None),
    "gift": ("🧧", None),
    "star": ("⭐️", None),
    "gear": ("⚙️", None),
    "film": ("🎬", None),
}


def build_premium_text(parts: list[tuple[str | None, str]]) -> tuple[str, list[MessageEntity]]:
    """parts: (emoji_nomi_yoki_None, matn) juftliklar ro'yxati.

    emoji_nomi berilса — o'sha joyga premium emoji (yoki fallback) qo'yiladi.
    Qaytadi: (to'liq_matn, entities). custom_emoji_id yo'q bo'lsa entity qo'shilmaydi."""
    text = ""
    entities: list[MessageEntity] = []
    for name, chunk in parts:
        if name and name in CUSTOM_EMOJI:
            fallback, emoji_id = CUSTOM_EMOJI[name]
            offset = len(text.encode("utf-16-le")) // 2  # Telegram UTF-16 hisoblaydi
            text += fallback
            if emoji_id:
                length = len(fallback.encode("utf-16-le")) // 2
                entities.append(
                    MessageEntity(
                        type="custom_emoji",
                        offset=offset,
                        length=length,
                        custom_emoji_id=emoji_id,
                    )
                )
        text += chunk
    return text, entities
