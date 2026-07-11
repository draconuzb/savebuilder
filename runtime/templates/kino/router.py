"""Kino shablon — oxirgi user oqimi (kod → kino)."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from db.models import ChildUser, KinoContent
from db.session import get_session
from runtime.templates.base import child_is_subscribed


def build_user_router(child_bot_id: int) -> Router:
    router = Router(name=f"kino-user-{child_bot_id}")

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
        if not await child_is_subscribed(bot, child_bot_id, message.from_user.id):
            await message.answer("‼️ Botdan foydalanish uchun kanal(lar)ga obuna bo'ling.")
            return
        await message.answer("🎬 Salom! Kino <b>kodini</b> yuboring.")

    @router.message(F.text & ~F.text.startswith("/"))
    async def get_by_code(message: Message, bot: Bot) -> None:
        if not await child_is_subscribed(bot, child_bot_id, message.from_user.id):
            await message.answer("‼️ Avval kanal(lar)ga obuna bo'ling.")
            return
        code = message.text.strip()
        async with get_session() as s:
            res = await s.execute(
                select(KinoContent).where(
                    KinoContent.child_bot_id == child_bot_id,
                    KinoContent.code == code,
                )
            )
            film = res.scalar_one_or_none()
            if film:
                film.views += 1
        if film is None:
            await message.answer("❌ Bunday kod topilmadi.")
            return
        await message.answer_video(film.file_id, caption=film.title or "🎬")

    return router
