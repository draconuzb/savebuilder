"""Super-admin dev buyruqlari (test balans, statistika)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import func, select

from core.config import get_settings
from db.models import ChildBot, User
from db.session import get_session
from manager.handlers.start import get_or_create_user
from manager.services.billing import top_up

router = Router(name="manager-admin")


def _is_super(tg_id: int) -> bool:
    return tg_id in get_settings().super_admin_ids


@router.message(Command("topup"))
async def topup_cmd(message: Message, command: CommandObject) -> None:
    """/topup <miqdor> — o'z balansiga qo'shish (faqat super-admin, test)."""
    if not _is_super(message.from_user.id):
        return
    try:
        amount = Decimal((command.args or "").strip())
    except (InvalidOperation, AttributeError):
        await message.answer("Foydalanish: <code>/topup 100000</code>")
        return
    user = await get_or_create_user(message)
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.id == user.id))).scalar_one()
        await top_up(s, u, amount, provider="admin")
        new_balance = u.balance
    await message.answer(f"✅ Balans to'ldirildi. Yangi balans: <b>{new_balance:,.0f}</b> so'm")


@router.message(Command("stats"))
async def stats_cmd(message: Message) -> None:
    """/stats — umumiy platforma statistikasi (super-admin)."""
    if not _is_super(message.from_user.id):
        return
    async with get_session() as s:
        users = await s.scalar(select(func.count(User.id)))
        bots = await s.scalar(select(func.count(ChildBot.id)))
        active = await s.scalar(
            select(func.count(ChildBot.id)).where(ChildBot.status == "active")
        )
    await message.answer(
        f"📊 <b>Platforma statistikasi</b>\n\n"
        f"👥 Mijozlar: <b>{users or 0}</b>\n"
        f"🤖 Botlar: <b>{bots or 0}</b> (aktiv: {active or 0})"
    )
