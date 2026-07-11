"""Telegram Stars (XTR) to'lovi — native balans to'ldirish (Bot API 7.5+).

Click/Payme merchant shart emas — foydalanuvchi to'g'ridan-to'g'ri Telegram
Stars bilan to'laydi, biz balansini so'mda to'ldiramiz."""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import LabeledPrice

# Stars → so'm balans paketlari: (stars, som)
STAR_PACKAGES: list[tuple[int, int]] = [
    (50, 10_000),
    (100, 20_000),
    (250, 50_000),
    (500, 100_000),
    (1000, 200_000),
]

PAYLOAD_PREFIX = "topup"


def payload_for(som: int) -> str:
    return f"{PAYLOAD_PREFIX}:{som}"


def parse_payload(payload: str) -> int | None:
    """topup:<som> payload'dan so'm miqdorini qaytaradi."""
    parts = payload.split(":")
    if len(parts) == 2 and parts[0] == PAYLOAD_PREFIX:
        try:
            return int(parts[1])
        except ValueError:
            return None
    return None


async def send_topup_invoice(bot: Bot, chat_id: int, stars: int, som: int) -> None:
    """Stars invoice yuborish (currency=XTR, provider_token bo'sh)."""
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"{som:,} so'm balans".replace(",", " "),
        description=f"SaveBuilder balansingizni {som:,} so'mga to'ldirish".replace(",", " "),
        payload=payload_for(som),
        currency="XTR",
        prices=[LabeledPrice(label=f"{som:,} so'm".replace(",", " "), amount=stars)],
        provider_token="",
    )
