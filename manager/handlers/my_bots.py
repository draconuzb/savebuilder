"""«🤖 Botlarim» — bola botlarni boshqarish (to'xtatish/yoqish/o'chirish/uzaytirish)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import delete, select

from core.constants import ChildBotStatus
from db.models import (
    ChildBot,
    ChildUser,
    ForceChannel,
    KinoContent,
    Tariff,
    Template,
    User,
)
from db.session import get_session
from manager import texts

router = Router(name="manager-mybots")
log = logging.getLogger(__name__)


async def _owner_bot(tg_id: int, child_id: int) -> ChildBot | None:
    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == tg_id))
        ).scalar_one_or_none()
        if not user:
            return None
        res = await s.execute(
            select(ChildBot).where(
                ChildBot.id == child_id, ChildBot.owner_id == user.id
            )
        )
        return res.scalar_one_or_none()


def _list_kb(bots: list[ChildBot]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for bot in bots:
        icon = "🟢" if bot.status == ChildBotStatus.ACTIVE else "⏸"
        b.row(
            InlineKeyboardButton(
                text=f"{icon} @{bot.bot_username or bot.id}",
                callback_data=f"mb:view:{bot.id}",
            )
        )
    return b.as_markup()


def _manage_kb(bot: ChildBot) -> InlineKeyboardMarkup:
    rows = []
    if bot.status == ChildBotStatus.ACTIVE:
        rows.append([InlineKeyboardButton(text="⏸ To'xtatish", callback_data=f"mb:stop:{bot.id}")])
    else:
        rows.append([InlineKeyboardButton(text="▶️ Yoqish", callback_data=f"mb:start:{bot.id}")])
    rows.append([InlineKeyboardButton(text="🔄 Tarifni uzaytirish", callback_data=f"mb:ext:{bot.id}")])
    rows.append([InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"mb:del:{bot.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="mb:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_bot(bot: ChildBot) -> str:
    async with get_session() as s:
        tpl = (
            await s.execute(select(Template).where(Template.id == bot.template_id))
        ).scalar_one_or_none()
        tariff = (
            await s.execute(select(Tariff).where(Tariff.id == bot.tariff_id))
        ).scalar_one_or_none()
    exp = bot.expires_at.strftime("%Y-%m-%d") if bot.expires_at else "—"
    return (
        f"🤖 <b>@{bot.bot_username}</b>\n\n"
        f"📦 Shablon: {tpl.title if tpl else '—'}\n"
        f"🎟 Tarif: {tariff.name if tariff else '—'}\n"
        f"📅 Amal qiladi: <b>{exp}</b>\n"
        f"⚙️ Holat: <b>{bot.status}</b>"
    )


@router.message(F.text == "🤖 Botlarim")
async def my_bots(message: Message) -> None:
    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == message.from_user.id))
        ).scalar_one_or_none()
        bots = []
        if user:
            r = await s.execute(select(ChildBot).where(ChildBot.owner_id == user.id))
            bots = r.scalars().all()
    if not bots:
        await message.answer(texts.MY_BOTS_EMPTY)
        return
    await message.answer("🤖 <b>Botlarim</b>\n\nBoshqarish uchun tanlang:", reply_markup=_list_kb(bots))


@router.callback_query(F.data == "mb:list")
async def back_to_list(cq: CallbackQuery) -> None:
    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == cq.from_user.id))
        ).scalar_one_or_none()
        bots = []
        if user:
            r = await s.execute(select(ChildBot).where(ChildBot.owner_id == user.id))
            bots = r.scalars().all()
    await cq.message.edit_text(
        "🤖 <b>Botlarim</b>\n\nBoshqarish uchun tanlang:", reply_markup=_list_kb(bots)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("mb:view:"))
async def view_bot(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    bot = await _owner_bot(cq.from_user.id, child_id)
    if not bot:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    await cq.message.edit_text(await _render_bot(bot), reply_markup=_manage_kb(bot))
    await cq.answer()


@router.callback_query(F.data.startswith("mb:stop:"))
async def stop_bot(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    bot = await _owner_bot(cq.from_user.id, child_id)
    if not bot:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    from runtime.loader import unregister_child_bot

    await unregister_child_bot(bot.webhook_secret)
    async with get_session() as s:
        obj = (await s.execute(select(ChildBot).where(ChildBot.id == child_id))).scalar_one()
        obj.status = ChildBotStatus.STOPPED
    bot.status = ChildBotStatus.STOPPED
    await cq.message.edit_text(await _render_bot(bot), reply_markup=_manage_kb(bot))
    await cq.answer("⏸ To'xtatildi")


@router.callback_query(F.data.startswith("mb:start:"))
async def start_bot(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    bot = await _owner_bot(cq.from_user.id, child_id)
    if not bot:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    async with get_session() as s:
        obj = (await s.execute(select(ChildBot).where(ChildBot.id == child_id))).scalar_one()
        obj.status = ChildBotStatus.ACTIVE
    from runtime.loader import register_child_bot

    try:
        await register_child_bot(child_id)
    except Exception as e:  # noqa: BLE001
        log.exception("start_bot register xato: %s", e)
        await cq.answer("Webhook xato. Admin tekshiradi.", show_alert=True)
        return
    bot.status = ChildBotStatus.ACTIVE
    await cq.message.edit_text(await _render_bot(bot), reply_markup=_manage_kb(bot))
    await cq.answer("▶️ Yoqildi")


@router.callback_query(F.data.startswith("mb:del:"))
async def del_confirm(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"mb:delyes:{child_id}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"mb:view:{child_id}"),
            ]
        ]
    )
    await cq.message.edit_text(
        "🗑 <b>Botni o'chirishni tasdiqlang</b>\n\nBarcha kontent va foydalanuvchilar o'chadi!",
        reply_markup=kb,
    )
    await cq.answer()


@router.callback_query(F.data.startswith("mb:delyes:"))
async def del_yes(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    bot = await _owner_bot(cq.from_user.id, child_id)
    if not bot:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    from runtime.loader import unregister_child_bot

    await unregister_child_bot(bot.webhook_secret)
    async with get_session() as s:
        await s.execute(delete(KinoContent).where(KinoContent.child_bot_id == child_id))
        await s.execute(delete(ChildUser).where(ChildUser.child_bot_id == child_id))
        await s.execute(delete(ForceChannel).where(ForceChannel.child_bot_id == child_id))
        await s.execute(delete(ChildBot).where(ChildBot.id == child_id))
    await cq.message.edit_text("🗑 Bot o'chirildi.")
    await cq.answer("O'chirildi")


@router.callback_query(F.data.startswith("mb:ext:"))
async def extend_tariff(cq: CallbackQuery) -> None:
    child_id = int(cq.data.split(":")[2])
    from manager.services.billing import (
        InsufficientBalance,
        charge,
        tariff_expiry,
    )

    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == cq.from_user.id))
        ).scalar_one_or_none()
        obj = (
            await s.execute(
                select(ChildBot).where(
                    ChildBot.id == child_id, ChildBot.owner_id == user.id
                )
            )
        ).scalar_one_or_none()
        if not obj:
            await cq.answer("Topilmadi.", show_alert=True)
            return
        tariff = (
            await s.execute(select(Tariff).where(Tariff.id == obj.tariff_id))
        ).scalar_one()
        try:
            await charge(s, user, tariff.price, purpose="tariff", child_bot_id=child_id)
        except InsufficientBalance as e:
            await cq.answer(
                f"Balans yetarli emas: kerak {e.need:,.0f}, bor {e.have:,.0f}",
                show_alert=True,
            )
            return
        obj.expires_at = tariff_expiry(tariff.duration_days)

    bot = await _owner_bot(cq.from_user.id, child_id)
    await cq.message.edit_text(await _render_bot(bot), reply_markup=_manage_kb(bot))
    await cq.answer(f"✅ {tariff.duration_days} kunga uzaytirildi")
