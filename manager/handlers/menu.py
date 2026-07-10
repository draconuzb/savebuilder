"""Asosiy menyu tugmalari: Hisobim, Botlarim, Pul kiritish, Referal, Qo'llanma, Support."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import func, select

from core.config import get_settings
from db.models import ChildBot, User
from db.session import get_session
from manager import texts

router = Router(name="manager-menu")


async def _get_user(tg_id: int) -> User | None:
    async with get_session() as s:
        res = await s.execute(select(User).where(User.tg_id == tg_id))
        return res.scalar_one_or_none()


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


@router.message(F.text == "🤖 Botlarim")
async def my_bots(message: Message) -> None:
    async with get_session() as s:
        res = await s.execute(select(User).where(User.tg_id == message.from_user.id))
        user = res.scalar_one_or_none()
        bots = []
        if user:
            r = await s.execute(select(ChildBot).where(ChildBot.owner_id == user.id))
            bots = r.scalars().all()
    if not bots:
        await message.answer(texts.MY_BOTS_EMPTY)
        return
    lines = ["🤖 <b>Botlarim</b>\n"]
    for b in bots:
        lines.append(f"• @{b.bot_username or '—'} — {b.status}")
    await message.answer("\n".join(lines))


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
