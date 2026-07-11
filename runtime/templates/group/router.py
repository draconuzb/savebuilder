"""Guruh salomlashuvchi bot — guruhga qo'shilgan yangi a'zolarni kutib oladi."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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

DEFAULT_WELCOME = "👋 Assalomu alaykum, {name}!\nGuruhga xush kelibsiz."


class SetWelcome(StatesGroup):
    waiting = State()


async def _get_welcome(child_bot_id: int) -> str:
    async with get_session() as s:
        cfg = await s.scalar(select(ChildBot.config).where(ChildBot.id == child_bot_id))
    return (cfg or {}).get("welcome", DEFAULT_WELCOME)


async def _set_welcome(child_bot_id: int, text: str) -> None:
    async with get_session() as s:
        cb = (await s.execute(select(ChildBot).where(ChildBot.id == child_bot_id))).scalar_one()
        cfg = dict(cb.config or {})
        cfg["welcome"] = text
        cb.config = cfg


def build_group_router(child_bot_id: int, owner_tg_id: int) -> Router:
    router = Router(name=f"group-{child_bot_id}")

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Salomlashuv matni", callback_data="grp:setwelcome", style="primary")],
            [InlineKeyboardButton(text="👀 Ko'rish", callback_data="grp:preview")],
        ]
    )

    @router.message(CommandStart(), F.chat.type == "private")
    async def start(message: Message) -> None:
        if message.from_user.id == owner_tg_id:
            await message.answer(
                "👑 <b>Guruh salomlashuvchi bot — admin</b>\n"
                "━━━━━━━━━━━━━━━\n"
                "1. Botni guruhingizga <b>admin</b> qilib qo'shing.\n"
                "2. Yangi a'zolar avtomatik kutib olinadi.\n\n"
                "Salomlashuv matnini sozlang 👇\n"
                "<i>{name} — a'zo ismi, {group} — guruh nomi</i>",
                reply_markup=admin_kb,
            )
        else:
            await message.answer("🤖 Bu bot guruhlarda yangi a'zolarni kutib oladi.")

    @router.callback_query(F.data == "grp:setwelcome")
    async def set_welcome_start(cq: CallbackQuery, state: FSMContext) -> None:
        if cq.from_user.id != owner_tg_id:
            return
        await state.set_state(SetWelcome.waiting)
        await cq.message.answer(
            "✏️ Yangi salomlashuv matnini yuboring.\n"
            "<i>{name} va {group} ishlatishingiz mumkin.</i>"
        )
        await cq.answer()

    @router.message(SetWelcome.waiting, F.text)
    async def set_welcome_save(message: Message, state: FSMContext) -> None:
        await state.clear()
        await _set_welcome(child_bot_id, message.text)
        await message.answer("✅ Salomlashuv matni saqlandi.", reply_markup=admin_kb)

    @router.callback_query(F.data == "grp:preview")
    async def preview(cq: CallbackQuery) -> None:
        text = await _get_welcome(child_bot_id)
        sample = text.replace("{name}", cq.from_user.full_name).replace("{group}", "Namuna guruh")
        await cq.message.answer(f"👀 <b>Namuna:</b>\n\n{sample}")
        await cq.answer()

    # Guruhga yangi a'zo qo'shildi
    @router.message(F.new_chat_members)
    async def greet(message: Message, bot: Bot) -> None:
        template = await _get_welcome(child_bot_id)
        for member in message.new_chat_members:
            if member.is_bot:
                continue
            mention = f'<a href="tg://user?id={member.id}">{member.full_name}</a>'
            text = template.replace("{name}", mention).replace("{group}", message.chat.title or "")
            try:
                await message.answer(text)
            except Exception as e:  # noqa: BLE001
                log.info("group greet xato: %s", e)

    return router
