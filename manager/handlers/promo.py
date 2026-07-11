"""Promokod ishlatish — tugma orqali (FSM) yoki /promo KOD buyrug'i."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.models import PromoCode, PromoRedemption, User
from db.session import get_session

router = Router(name="manager-promo")


class PromoRedeem(StatesGroup):
    waiting_code = State()


async def _redeem(message: Message, code: str) -> None:
    code = code.strip()
    if not code:
        await message.answer("❌ Promokod bo'sh.")
        return
    async with get_session() as s:
        promo = (
            await s.execute(select(PromoCode).where(PromoCode.code == code.upper()))
        ).scalar_one_or_none()
        if promo is None or not promo.is_active:
            await message.answer("❌ Bunday promokod topilmadi yoki faol emas.")
            return
        if promo.used_count >= promo.max_uses:
            await message.answer("❌ Bu promokod limiti tugagan.")
            return
        user = (
            await s.execute(select(User).where(User.tg_id == message.from_user.id))
        ).scalar_one_or_none()
        if user is None:
            await message.answer("Iltimos /start bosing.")
            return
        already = await s.scalar(
            select(PromoRedemption.id).where(
                PromoRedemption.promo_id == promo.id,
                PromoRedemption.user_id == user.id,
            )
        )
        if already:
            await message.answer("⚠️ Siz bu promokodni allaqachon ishlatgansiz.")
            return
        try:
            s.add(PromoRedemption(promo_id=promo.id, user_id=user.id))
            promo.used_count += 1
            user.balance += promo.amount
            new_balance = user.balance
            bonus = promo.amount
            await s.flush()
        except IntegrityError:
            await message.answer("⚠️ Siz bu promokodni allaqachon ishlatgansiz.")
            return
    await message.answer(
        "🎉 <b>Promokod qabul qilindi!</b>\n"
        f"💰 +{bonus:,.0f} so'm\n"
        f"Yangi balans: <b>{new_balance:,.0f}</b> so'm".replace(",", " ")
    )


@router.message(F.text == "🎁 Promokod")
async def promo_button(message: Message, state: FSMContext) -> None:
    await state.set_state(PromoRedeem.waiting_code)
    await message.answer("🎁 <b>Promokod</b>\n━━━━━━━━━━━━━━━\nPromokodingizni yuboring:")


@router.message(PromoRedeem.waiting_code, F.text)
async def promo_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _redeem(message, message.text)


@router.message(Command("promo"))
async def redeem_cmd(message: Message, command: CommandObject) -> None:
    await _redeem(message, command.args or "")
