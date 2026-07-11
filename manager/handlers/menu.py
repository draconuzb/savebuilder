"""Asosiy menyu tugmalari: Hisobim, Botlarim, Pul kiritish, Referal, Qo'llanma, Support."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select

from db.models import ChildBot, ReferralReward, User
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


@router.message(F.text == "💎 Referal")
async def referral(message: Message) -> None:
    me = (await message.bot.get_me()).username
    link = f"https://t.me/{me}?start=ref{message.from_user.id}"
    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == message.from_user.id))
        ).scalar_one_or_none()
        count = earned = 0
        if user:
            count = await s.scalar(
                select(func.count(User.id)).where(User.referred_by == user.id)
            ) or 0
            earned = await s.scalar(
                select(func.coalesce(func.sum(ReferralReward.amount), 0)).where(
                    ReferralReward.referrer_id == user.id
                )
            ) or 0
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Havolani nusxalash", copy_text=CopyTextButton(text=link))],
            [InlineKeyboardButton(text="📤 Ulashish", url=f"https://t.me/share/url?url={link}")],
        ]
    )
    await message.answer(
        "💎 <b>Referal dasturi</b>\n\n"
        "Do'stlaringizni taklif qiling — ular balans to'ldirganda "
        f"<b>{10}%</b> bonus olasiz!\n\n"
        f"🔗 Havolangiz:\n<code>{link}</code>\n\n"
        f"👥 Takliflar: <b>{count}</b>\n"
        f"💰 Ishlangan bonus: <b>{earned:,.0f}</b> so'm".replace(",", " "),
        reply_markup=kb,
    )


@router.message(F.text == "📖 Qo'llanma")
async def guide(message: Message) -> None:
    await message.answer(texts.GUIDE)


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(texts.GUIDE)


@router.message(F.text == "🧧 Qo'llab-quvvatlash")
async def support(message: Message) -> None:
    await message.answer(texts.SUPPORT)
