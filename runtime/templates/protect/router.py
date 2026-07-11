"""Guruh himoyachi (anti-spam) bot — oddiy a'zolarning havola/reklama/forward xabarlarini o'chiradi."""
from __future__ import annotations

import logging
import time

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select

from db.models import ChildBot
from db.session import get_session

log = logging.getLogger(__name__)

# chat_id -> (admin_id set, timestamp) — 5 daqiqa kesh
_admin_cache: dict[int, tuple[set[int], float]] = {}
_ADMIN_TTL = 300


async def _get_config(child_bot_id: int) -> dict:
    async with get_session() as s:
        cfg = await s.scalar(select(ChildBot.config).where(ChildBot.id == child_bot_id))
    c = dict(cfg or {})
    c.setdefault("del_links", True)
    c.setdefault("del_fwd", False)
    return c


async def _toggle(child_bot_id: int, key: str) -> bool:
    async with get_session() as s:
        cb = (await s.execute(select(ChildBot).where(ChildBot.id == child_bot_id))).scalar_one()
        cfg = dict(cb.config or {})
        cfg[key] = not cfg.get(key, key == "del_links")
        cb.config = cfg
        return cfg[key]


async def _is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    cached = _admin_cache.get(chat_id)
    if not cached or time.time() - cached[1] > _ADMIN_TTL:
        try:
            admins = await bot.get_chat_administrators(chat_id)
            ids = {a.user.id for a in admins}
        except Exception:  # noqa: BLE001
            ids = set()
        _admin_cache[chat_id] = (ids, time.time())
        cached = _admin_cache[chat_id]
    return user_id in cached[0]


def _has_link(message: Message) -> bool:
    ents = (message.entities or []) + (message.caption_entities or [])
    if any(e.type in ("url", "text_link", "mention") for e in ents):
        return True
    txt = (message.text or "") + " " + (message.caption or "")
    low = txt.lower()
    return "http://" in low or "https://" in low or "t.me/" in low or "@" in low


def build_protect_router(child_bot_id: int, owner_tg_id: int) -> Router:
    router = Router(name=f"protect-{child_bot_id}")

    async def panel_kb() -> InlineKeyboardMarkup:
        c = await _get_config(child_bot_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"🔗 Havolalarni o'chirish: {'✅' if c['del_links'] else '❌'}",
                    callback_data="prot:del_links",
                )],
                [InlineKeyboardButton(
                    text=f"↪️ Forwardlarni o'chirish: {'✅' if c['del_fwd'] else '❌'}",
                    callback_data="prot:del_fwd",
                )],
            ]
        )

    @router.message(CommandStart(), F.chat.type == "private")
    async def start(message: Message) -> None:
        if message.from_user.id == owner_tg_id:
            await message.answer(
                "🔒 <b>Guruh himoyachi — admin</b>\n"
                "━━━━━━━━━━━━━━━\n"
                "1. Botni guruhga <b>admin</b> qiling (xabar o'chirish huquqi bilan).\n"
                "2. Oddiy a'zolarning spam/havola xabarlari avtomatik o'chadi.\n\n"
                "Sozlamalar 👇",
                reply_markup=await panel_kb(),
            )
        else:
            await message.answer("🛡 Bu bot guruhingizni spam va reklamadan himoya qiladi.")

    @router.callback_query(F.data.startswith("prot:"))
    async def toggle(cq: CallbackQuery) -> None:
        if cq.from_user.id != owner_tg_id:
            return
        key = cq.data.split(":")[1]
        await _toggle(child_bot_id, key)
        await cq.message.edit_reply_markup(reply_markup=await panel_kb())
        await cq.answer("O'zgardi ✅")

    @router.message(F.chat.type.in_({"group", "supergroup"}))
    async def guard(message: Message, bot: Bot) -> None:
        if message.from_user is None:
            return
        if await _is_group_admin(bot, message.chat.id, message.from_user.id):
            return
        c = await _get_config(child_bot_id)
        is_fwd = bool(getattr(message, "forward_origin", None) or getattr(message, "forward_from", None))
        if (c["del_links"] and _has_link(message)) or (c["del_fwd"] and is_fwd):
            try:
                await message.delete()
            except Exception as e:  # noqa: BLE001
                log.info("protect delete xato: %s", e)

    return router
