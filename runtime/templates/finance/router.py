"""Valyuta kursi bot — O'zbekiston MB (CBU) bepul API'sidan kurslar."""
from __future__ import annotations

import logging
import time

import aiohttp
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select

from db.models import ChildUser
from db.session import get_session
from runtime.templates.base import child_is_subscribed

log = logging.getLogger(__name__)

CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
MAIN = ["USD", "EUR", "RUB", "KZT", "TRY", "GBP"]

# Umumiy kesh (barcha finance botlar uchun) — 1 soat TTL
_cache: dict[str, str] = {}
_cache_ts: float = 0.0
_TTL = 3600


async def _get_rates() -> dict[str, str]:
    global _cache, _cache_ts
    if _cache and time.time() - _cache_ts < _TTL:
        return _cache
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(CBU_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json(content_type=None)
        _cache = {item["Ccy"]: item["Rate"] for item in data}
        _cache_ts = time.time()
    except Exception as e:  # noqa: BLE001
        log.info("CBU kurs olishda xato: %s", e)
    return _cache


def _kb() -> InlineKeyboardMarkup:
    rows, row = [], []
    for c in MAIN:
        row.append(InlineKeyboardButton(text=c, callback_data=f"fx:{c}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="💱 Barcha asosiy", callback_data="fx:ALL", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_finance_router(child_bot_id: int, owner_tg_id: int) -> Router:
    router = Router(name=f"finance-{child_bot_id}")

    @router.message(CommandStart())
    async def start(message: Message, bot: Bot) -> None:
        async with get_session() as s:
            exists = await s.scalar(
                select(ChildUser.id).where(
                    ChildUser.child_bot_id == child_bot_id,
                    ChildUser.tg_id == message.from_user.id,
                )
            )
            if not exists:
                s.add(ChildUser(child_bot_id=child_bot_id, tg_id=message.from_user.id))
        if message.from_user.id != owner_tg_id and not await child_is_subscribed(
            bot, child_bot_id, message.from_user.id
        ):
            await message.answer("‼️ Botdan foydalanish uchun kanal(lar)ga obuna bo'ling.")
            return
        await message.answer(
            "💱 <b>Valyuta kurslari</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "Markaziy bank rasmiy kurslari (so'mda).\n"
            "Valyutani tanlang 👇",
            reply_markup=_kb(),
        )

    @router.callback_query(F.data.startswith("fx:"))
    async def show_rate(cq: CallbackQuery) -> None:
        rates = await _get_rates()
        if not rates:
            await cq.answer("Kurslarni olishda xato. Keyinroq urinib ko'ring.", show_alert=True)
            return
        which = cq.data.split(":")[1]
        if which == "ALL":
            lines = ["💱 <b>Asosiy kurslar</b> (so'm)", "━━━━━━━━━━━━━━━"]
            for c in MAIN:
                if c in rates:
                    lines.append(f"• <b>{c}</b>: {rates[c]}")
            await cq.message.answer("\n".join(lines))
        elif which in rates:
            await cq.message.answer(f"💵 <b>1 {which}</b> = <b>{rates[which]}</b> so'm")
        else:
            await cq.answer("Bunday valyuta yo'q.", show_alert=True)
            return
        await cq.answer()

    return router
