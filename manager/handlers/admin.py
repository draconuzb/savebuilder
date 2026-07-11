"""Super-admin paneli: platforma statistikasi, ommaviy xabar, shablonlar, daromad."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select

from core.config import get_settings
from db.models import ChildBot, Payment, Template, User
from db.session import get_session
from manager.handlers.start import get_or_create_user
from manager.services.billing import top_up

router = Router(name="manager-admin")
log = logging.getLogger(__name__)


class AdminCast(StatesGroup):
    waiting_message = State()
    confirming = State()


def _is_super(tg_id: int) -> bool:
    return tg_id in get_settings().super_admin_ids


def _panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats", style="primary"),
                InlineKeyboardButton(text="💰 Daromad", callback_data="adm:rev", style="success"),
            ],
            [InlineKeyboardButton(text="📦 Shablonlar", callback_data="adm:tpls")],
            [InlineKeyboardButton(text="📢 Ommaviy xabar", callback_data="adm:cast", style="primary")],
        ]
    )


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not _is_super(message.from_user.id):
        return
    await message.answer("👑 <b>Super-admin panel</b>", reply_markup=_panel_kb())


@router.callback_query(F.data == "adm:back")
async def back(cq: CallbackQuery) -> None:
    await cq.message.edit_text("👑 <b>Super-admin panel</b>", reply_markup=_panel_kb())
    await cq.answer()


@router.callback_query(F.data == "adm:stats")
async def stats(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    async with get_session() as s:
        users = await s.scalar(select(func.count(User.id)))
        bots = await s.scalar(select(func.count(ChildBot.id)))
        active = await s.scalar(
            select(func.count(ChildBot.id)).where(ChildBot.status == "active")
        )
        verified = await s.scalar(
            select(func.count(User.id)).where(User.is_verified.is_(True))
        )
    await cq.message.edit_text(
        f"📊 <b>Platforma statistikasi</b>\n\n"
        f"👥 Mijozlar: <b>{users or 0}</b> (tasdiqlangan: {verified or 0})\n"
        f"🤖 Botlar: <b>{bots or 0}</b> (aktiv: {active or 0})",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")]]
        ),
    )
    await cq.answer()


@router.callback_query(F.data == "adm:rev")
async def revenue(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    async with get_session() as s:
        total = await s.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "paid")
        )
        rows = (
            await s.execute(
                select(Payment.purpose, func.coalesce(func.sum(Payment.amount), 0))
                .where(Payment.status == "paid")
                .group_by(Payment.purpose)
            )
        ).all()
    lines = [f"💰 <b>Daromad</b>\n\nJami: <b>{total or 0:,.0f}</b> so'm\n".replace(",", " ")]
    for purpose, amount in rows:
        lines.append(f"• {purpose}: {amount:,.0f} so'm".replace(",", " "))
    await cq.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")]]
        ),
    )
    await cq.answer()


@router.callback_query(F.data == "adm:tpls")
async def templates_list(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    async with get_session() as s:
        tpls = (await s.execute(select(Template).order_by(Template.id))).scalars().all()
    rows = []
    for t in tpls:
        mark = "🟢" if t.is_active else "🔴"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {t.title} ({t.create_price:,.0f})".replace(",", " "), callback_data=f"adm:tpl:{t.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")])
    await cq.message.edit_text(
        "📦 <b>Shablonlar</b>\n\nHolatini almashtirish uchun bosing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("adm:tpl:"))
async def toggle_template(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    tid = int(cq.data.split(":")[2])
    async with get_session() as s:
        t = (await s.execute(select(Template).where(Template.id == tid))).scalar_one_or_none()
        if t:
            t.is_active = not t.is_active
    await cq.answer("Holat o'zgardi")
    await templates_list(cq)


# ---- Ommaviy xabar (barcha mijozlarga) ----
@router.callback_query(F.data == "adm:cast")
async def cast_start(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminCast.waiting_message)
    await cq.message.edit_text("📢 Barcha mijozlarga yuboriladigan xabarni yuboring:")
    await cq.answer()


@router.message(AdminCast.waiting_message)
async def cast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(AdminCast.confirming)
    async with get_session() as s:
        cnt = await s.scalar(select(func.count(User.id)))
    await message.answer(
        f"👥 <b>{cnt or 0}</b> mijozga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yuborish", callback_data="adm:castgo", style="success"),
                    InlineKeyboardButton(text="❌ Bekor", callback_data="adm:back", style="danger"),
                ]
            ]
        ),
    )


@router.callback_query(AdminCast.confirming, F.data == "adm:castgo")
async def cast_go(cq: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await cq.message.edit_text("📤 Yuborilmoqda...")
    async with get_session() as s:
        ids = [r[0] for r in (await s.execute(select(User.tg_id))).all()]
    sent = failed = 0
    for uid in ids:
        try:
            await cq.bot.copy_message(chat_id=uid, from_chat_id=data["from_chat_id"], message_id=data["message_id"])
            sent += 1
        except Exception:  # noqa: BLE001
            failed += 1
        await asyncio.sleep(0.05)
    await cq.message.answer(f"✅ Tugadi. Yuborildi: <b>{sent}</b> · Xato: <b>{failed}</b>", reply_markup=_panel_kb())
    await cq.answer()


# ---- Test balans (dev) ----
@router.message(Command("topup"))
async def topup_cmd(message: Message, command: CommandObject) -> None:
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
    await message.answer(f"✅ Balans: <b>{new_balance:,.0f}</b> so'm".replace(",", " "))
