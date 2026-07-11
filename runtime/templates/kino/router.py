"""Media-kod shabloni — oxirgi user oqimi (kod → media). Kino/Audio umumiy."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from db.models import ChildUser, KinoContent
from db.session import get_session
from runtime.templates.base import child_is_subscribed
from runtime.templates.media_spec import KINO, MediaSpec


async def _send_media(message: Message, film: KinoContent) -> None:
    if film.media_type == "audio":
        await message.answer_audio(film.file_id, caption=film.title or "🎵")
    elif film.media_type == "document":
        await message.answer_document(film.file_id, caption=film.title or "📄")
    else:
        await message.answer_video(film.file_id, caption=film.title or "🎬")


def build_user_router(child_bot_id: int, spec: MediaSpec = KINO) -> Router:
    router = Router(name=f"media-user-{child_bot_id}")

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
        await message.answer(
            f"{spec.emoji} <b>Assalomu alaykum!</b>\n"
            "━━━━━━━━━━━━━━━\n"
            f"Kerakli {spec.noun.lower()}ning <b>kodini</b> yuboring 👇\n"
            "<i>Kod raqamlardan iborat bo'ladi.</i>"
        )

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
            await message.answer("❌ <b>Bunday kod topilmadi.</b>\nKodni tekshirib, qayta yuboring.")
            return
        await _send_media(message, film)

    return router
