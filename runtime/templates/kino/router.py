"""Kino shablon: oxirgi user (kod → kino) va admin (kino qo'shish) oqimlari."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from db.models import ChildBot, ChildUser, KinoContent
from db.session import get_session
from runtime.templates.base import child_is_subscribed


class AddKino(StatesGroup):
    waiting_code = State()
    waiting_video = State()


def build_kino_router(child_bot_id: int, owner_tg_id: int) -> Router:
    """Har bola bot uchun alohida router (child_bot_id ga bog'langan)."""
    router = Router(name=f"kino-{child_bot_id}")

    def is_owner(msg: Message) -> bool:
        return msg.from_user.id == owner_tg_id

    @router.message(CommandStart())
    async def start(message: Message, bot: Bot) -> None:
        # Userni ro'yxatga olish
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

    @router.message(Command("admin"))
    async def admin(message: Message) -> None:
        if not is_owner(message):
            return
        async with get_session() as s:
            films = await s.scalar(
                select(func.count(KinoContent.id)).where(
                    KinoContent.child_bot_id == child_bot_id
                )
            )
            users = await s.scalar(
                select(func.count(ChildUser.id)).where(
                    ChildUser.child_bot_id == child_bot_id
                )
            )
        await message.answer(
            f"⚙️ <b>Admin panel</b>\n\n"
            f"🎬 Kinolar: <b>{films or 0}</b>\n"
            f"👥 Foydalanuvchilar: <b>{users or 0}</b>\n\n"
            f"➕ Kino qo'shish: /add"
        )

    @router.message(Command("add"))
    async def add_start(message: Message, state: FSMContext) -> None:
        if not is_owner(message):
            return
        await state.set_state(AddKino.waiting_code)
        await message.answer("Yangi kino uchun <b>kod</b> yuboring (masalan: 123):")

    @router.message(AddKino.waiting_code, F.text)
    async def add_code(message: Message, state: FSMContext) -> None:
        await state.update_data(code=message.text.strip())
        await state.set_state(AddKino.waiting_video)
        await message.answer("Endi <b>video</b> faylini yuboring:")

    @router.message(AddKino.waiting_video, F.video)
    async def add_video(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        async with get_session() as s:
            s.add(
                KinoContent(
                    child_bot_id=child_bot_id,
                    code=data["code"],
                    title=message.caption,
                    file_id=message.video.file_id,
                )
            )
        await state.clear()
        await message.answer(f"✅ Kino saqlandi. Kod: <code>{data['code']}</code>")

    @router.message(F.text)
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
