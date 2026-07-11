"""Asosiy menyu tugmalari: Hisobim, Botlarim, Pul kiritish, Referal, Qo'llanma, Support."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import func, select

from db.models import ChildBot, User
from db.session import get_session
from manager import texts

router = Router(name="manager-menu")


@router.message(F.text == "📇 Hisobim")
async def account(message: Message) -> None:
    async with get_session() as s:
        res = await s.execute(select(User).where(User.tg_id == message.from_user.id))
        user = res.scalar_one_or_none()
        if user is None:
            await message.answer("Iltimos /start bosing.")
            return
        cnt = await s.scalar(
            select(func.count(ChildBot.id)).where(ChildBot.owner_id == user.id)
        )
    await message.answer(
        texts.ACCOUNT.format(
            name=message.from_user.full_name,
            tg_id=message.from_user.id,
            balance=user.balance,
            bots=cnt or 0,
        )
    )


@router.message(F.text == "💳 Pul kiritish")
async def topup(message: Message) -> None:
    await message.answer(texts.TOPUP)


@router.message(F.text == "💎 Referal")
async def referral(message: Message) -> None:
    me = (await message.bot.get_me()).username
    link = f"https://t.me/{me}?start=ref{message.from_user.id}"
    await message.answer(texts.REFERRAL.format(link=link, count=0))


@router.message(F.text == "📖 Qo'llanma")
async def guide(message: Message) -> None:
    await message.answer(texts.GUIDE)


@router.message(F.text == "🧧 Qo'llab-quvvatlash")
async def support(message: Message) -> None:
    await message.answer(texts.SUPPORT)
