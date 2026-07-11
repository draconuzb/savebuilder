"""Anonim xabar bot shabloni — userlar egaga anonim yozadi, ega anonim javob beradi."""
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

from db.models import ChildUser
from db.session import get_session
from runtime.templates.base import child_is_subscribed

log = logging.getLogger(__name__)


class AnonReply(StatesGroup):
    waiting = State()


def build_anon_router(child_bot_id: int, owner_tg_id: int) -> Router:
    router = Router(name=f"anon-{child_bot_id}")

    def reply_kb(sender_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Javob berish", callback_data=f"anon:reply:{sender_id}", style="primary")]
            ]
        )

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
        if message.from_user.id == owner_tg_id:
            await message.answer(
                "👑 <b>Anonim xabar bot — admin</b>\n"
                "━━━━━━━━━━━━━━━\n"
                "Sizga kelgan anonim xabarlar shu yerda ko'rinadi.\n"
                "Har xabar ostidagi «✍️ Javob berish» tugmasi orqali anonim javob bering."
            )
            return
        if not await child_is_subscribed(bot, child_bot_id, message.from_user.id):
            await message.answer("‼️ Botdan foydalanish uchun kanal(lar)ga obuna bo'ling.")
            return
        await message.answer(
            "🕵️ <b>Anonim xabar</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "Xabaringizni yozing — u <b>anonim</b> tarzda yetkaziladi.\n"
            "<i>Matn, rasm, video, ovozli — hammasi mumkin.</i>"
        )

    # Ega javob berish tugmasini bosdi
    @router.callback_query(F.data.startswith("anon:reply:"))
    async def reply_start(cq: CallbackQuery, state: FSMContext) -> None:
        if cq.from_user.id != owner_tg_id:
            await cq.answer("Faqat admin javob bera oladi.", show_alert=True)
            return
        sender_id = int(cq.data.split(":")[2])
        await state.set_state(AnonReply.waiting)
        await state.update_data(target=sender_id)
        await cq.message.answer("✍️ Javobingizni yozing (anonim yuboriladi):")
        await cq.answer()

    # Ega javobini yubordi
    @router.message(AnonReply.waiting)
    async def reply_send(message: Message, state: FSMContext, bot: Bot) -> None:
        data = await state.get_data()
        await state.clear()
        target = data.get("target")
        if not target:
            return
        try:
            await bot.send_message(target, "📨 <b>Sizga anonim javob keldi:</b>")
            await bot.copy_message(chat_id=target, from_chat_id=message.chat.id, message_id=message.message_id)
            await message.answer("✅ Javob yuborildi.")
        except Exception as e:  # noqa: BLE001
            log.info("anon reply xato: %s", e)
            await message.answer("❌ Yuborib bo'lmadi (user botni bloklagan bo'lishi mumkin).")

    # Oddiy user xabar yubordi -> egaga anonim yetkazish
    @router.message(F.from_user.id != owner_tg_id)
    async def forward_to_owner(message: Message, bot: Bot) -> None:
        if not await child_is_subscribed(bot, child_bot_id, message.from_user.id):
            await message.answer("‼️ Avval kanal(lar)ga obuna bo'ling.")
            return
        try:
            await bot.send_message(owner_tg_id, "📩 <b>Yangi anonim xabar:</b>")
            await bot.copy_message(
                chat_id=owner_tg_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=reply_kb(message.from_user.id),
            )
            await message.answer("✅ Xabaringiz anonim yuborildi.")
        except Exception as e:  # noqa: BLE001
            log.info("anon forward xato: %s", e)
            await message.answer("❌ Xabar yuborilmadi. Keyinroq urinib ko'ring.")

    return router
