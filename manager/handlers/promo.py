"""Foydalanuvchi uchun promokod ishlatish (/promo CODE)."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.models import PromoCode, PromoRedemption, User
from db.session import get_session

router = Router(name="manager-promo")


@router.message(Command("promo"))
async def redeem_promo(message: Message, command: CommandObject) -> None:
    code = (command.args or "").strip()
    if not code:
        await message.answer("🎁 Foydalanish: <code>/promo KOD</code>")
        return

    async with get_session() as s:
        promo = (
            await s.execute(select(PromoCode).where(PromoCode.code == code))
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
        f"🎉 <b>Promokod qabul qilindi!</b>\n"
        f"💰 +{bonus:,.0f} so'm\n"
        f"Yangi balans: <b>{new_balance:,.0f}</b> so'm".replace(",", " ")
    )
