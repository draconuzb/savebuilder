"""So'rovnoma / Viktorina bot — ega poll yaratadi, barcha userlarga tarqatiladi (native Telegram poll)."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputPollOption,
    Message,
)
from sqlalchemy import func, select

from db.models import ChildUser
from db.session import get_session

log = logging.getLogger(__name__)


class NewPoll(StatesGroup):
    question = State()
    options = State()
    correct = State()


def build_poll_router(child_bot_id: int, owner_tg_id: int, is_quiz: bool) -> Router:
    router = Router(name=f"poll-{child_bot_id}")
    noun = "Viktorina" if is_quiz else "So'rovnoma"
    emoji = "🧠" if is_quiz else "📊"

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"➕ Yangi {noun.lower()}", callback_data="poll:new", style="success")]]
    )

    @router.message(CommandStart())
    async def start(message: Message) -> None:
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
            async with get_session() as s:
                cnt = await s.scalar(select(func.count(ChildUser.id)).where(ChildUser.child_bot_id == child_bot_id))
            await message.answer(
                f"👑 <b>{noun} bot — admin</b>\n"
                "━━━━━━━━━━━━━━━\n"
                f"👥 Obunachilar: <b>{cnt or 0}</b>\n\n"
                f"Yangi {noun.lower()} yaratib, barchaga tarqating 👇",
                reply_markup=admin_kb,
            )
        else:
            await message.answer(f"{emoji} Salom! Bu yerda {noun.lower()}larда qatnashasiz.")

    @router.callback_query(F.data == "poll:new")
    async def new_poll(cq: CallbackQuery, state: FSMContext) -> None:
        if cq.from_user.id != owner_tg_id:
            return
        await state.set_state(NewPoll.question)
        await cq.message.answer(f"{emoji} <b>Savolni</b> yuboring:")
        await cq.answer()

    @router.message(NewPoll.question, F.text)
    async def got_question(message: Message, state: FSMContext) -> None:
        await state.update_data(question=message.text.strip())
        await state.set_state(NewPoll.options)
        await message.answer(
            "📝 <b>Variantlarni</b> yuboring — har birini <b>alohida qatorda</b> "
            "(2 tadan 10 tagacha):"
        )

    @router.message(NewPoll.options, F.text)
    async def got_options(message: Message, state: FSMContext, bot: Bot) -> None:
        opts = [ln.strip() for ln in message.text.splitlines() if ln.strip()]
        if len(opts) < 2:
            await message.answer("❌ Kamida 2 ta variant kerak.")
            return
        opts = opts[:10]
        await state.update_data(options=opts)
        if is_quiz:
            await state.set_state(NewPoll.correct)
            numbered = "\n".join(f"{i+1}. {o}" for i, o in enumerate(opts))
            await message.answer(f"✅ To'g'ri javob raqamini yuboring:\n\n{numbered}")
        else:
            await _broadcast_poll(message, state, bot, correct=None)

    @router.message(NewPoll.correct, F.text)
    async def got_correct(message: Message, state: FSMContext, bot: Bot) -> None:
        data = await state.get_data()
        if not message.text.strip().isdigit():
            await message.answer("❌ Raqam yuboring.")
            return
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(data["options"]):
            await message.answer("❌ Noto'g'ri raqam.")
            return
        await _broadcast_poll(message, state, bot, correct=idx)

    async def _broadcast_poll(message: Message, state: FSMContext, bot: Bot, correct: int | None) -> None:
        data = await state.get_data()
        await state.clear()
        await message.answer("📤 Tarqatilmoqda...")
        async with get_session() as s:
            ids = [r[0] for r in (await s.execute(
                select(ChildUser.tg_id).where(ChildUser.child_bot_id == child_bot_id)
            )).all()]
        options = [InputPollOption(text=o) for o in data["options"]]
        sent = failed = 0
        for uid in ids:
            try:
                await bot.send_poll(
                    chat_id=uid,
                    question=data["question"],
                    options=options,
                    is_anonymous=True,
                    type="quiz" if is_quiz else "regular",
                    correct_option_id=correct if is_quiz else None,
                )
                sent += 1
            except Exception:  # noqa: BLE001
                failed += 1
            await asyncio.sleep(0.05)
        await message.answer(f"✅ Tarqatildi: <b>{sent}</b> · Xato: <b>{failed}</b>", reply_markup=admin_kb)

    return router
