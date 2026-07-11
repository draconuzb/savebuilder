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
from db.models import ChildBot, Payment, PromoCode, Template, User
from db.session import get_session
from manager.handlers.start import get_or_create_user
from manager.services.billing import top_up

router = Router(name="manager-admin")
log = logging.getLogger(__name__)


class AdminCast(StatesGroup):
    waiting_message = State()
    confirming = State()


class AdminUser(StatesGroup):
    waiting_query = State()
    waiting_add = State()
    waiting_deduct = State()


class AdminTpl(StatesGroup):
    waiting_price = State()


class AdminPromo(StatesGroup):
    waiting_code = State()
    waiting_amount = State()
    waiting_max = State()


def _is_super(tg_id: int) -> bool:
    return tg_id in get_settings().super_admin_ids


def _panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats", style="primary"),
                InlineKeyboardButton(text="💰 Daromad", callback_data="adm:rev", style="success"),
            ],
            [
                InlineKeyboardButton(text="👥 Userlar", callback_data="adm:users", style="primary"),
                InlineKeyboardButton(text="📦 Shablonlar", callback_data="adm:tpls"),
            ],
            [
                InlineKeyboardButton(text="🎁 Promokodlar", callback_data="adm:promo", style="success"),
                InlineKeyboardButton(text="📢 Xabar", callback_data="adm:cast", style="primary"),
            ],
        ]
    )


def _back_kb(cb: str = "adm:back") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=cb)]]
    )


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not _is_super(message.from_user.id):
        return
    from manager.texts import premiumize

    await message.answer(premiumize("👑 <b>Super-admin panel</b>"), reply_markup=_panel_kb())


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


def _tpl_card_kb(t: Template) -> InlineKeyboardMarkup:
    toggle = (
        InlineKeyboardButton(text="🔴 Nofaol qilish", callback_data=f"adm:tpltgl:{t.id}", style="danger")
        if t.is_active
        else InlineKeyboardButton(text="🟢 Faollashtirish", callback_data=f"adm:tpltgl:{t.id}", style="success")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Narxni o'zgartirish", callback_data=f"adm:tplprice:{t.id}", style="primary")],
            [toggle],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:tpls")],
        ]
    )


async def _show_tpl_card(cq: CallbackQuery, tid: int) -> None:
    async with get_session() as s:
        t = (await s.execute(select(Template).where(Template.id == tid))).scalar_one_or_none()
    if not t:
        await cq.answer("Topilmadi", show_alert=True)
        return
    txt = (
        f"{t.title}\n━━━━━━━━━━━━━━━\n"
        f"├ 🏷 Kod: <code>{t.code}</code>\n"
        f"├ 💰 Narx: <b>{t.create_price:,.0f}</b> so'm\n"
        f"├ 🗂 Kategoriya: {t.category}\n"
        f"└ {'🟢 Faol' if t.is_active else '🔴 Nofaol'}"
    ).replace(",", " ")
    await cq.message.edit_text(txt, reply_markup=_tpl_card_kb(t))


@router.callback_query(F.data.startswith("adm:tpl:"))
async def template_card(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    await _show_tpl_card(cq, int(cq.data.split(":")[2]))
    await cq.answer()


@router.callback_query(F.data.startswith("adm:tpltgl:"))
async def template_toggle(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    tid = int(cq.data.split(":")[2])
    async with get_session() as s:
        t = (await s.execute(select(Template).where(Template.id == tid))).scalar_one_or_none()
        if t:
            t.is_active = not t.is_active
    await cq.answer("Holat o'zgardi")
    await _show_tpl_card(cq, tid)


@router.callback_query(F.data.startswith("adm:tplprice:"))
async def template_price_start(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminTpl.waiting_price)
    await state.update_data(tid=int(cq.data.split(":")[2]))
    await cq.message.answer("✏️ Yangi ochish narxini yuboring (masalan 80000):")
    await cq.answer()


@router.message(AdminTpl.waiting_price, F.text)
async def template_price_set(message: Message, state: FSMContext) -> None:
    if not _is_super(message.from_user.id):
        return
    data = await state.get_data()
    await state.clear()
    try:
        price = Decimal(message.text.strip())
    except (InvalidOperation, AttributeError):
        await message.answer("❌ Noto'g'ri son.")
        return
    async with get_session() as s:
        t = (await s.execute(select(Template).where(Template.id == data["tid"]))).scalar_one_or_none()
        if t:
            t.create_price = price
            title = t.title
    await message.answer(f"✅ {title} narxi <b>{price:,.0f}</b> so'm qilib o'zgartirildi.".replace(",", " "))


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


# ---- Userlar boshqaruvi ----
async def _find_user(query: str) -> User | None:
    query = query.strip().lstrip("@")
    async with get_session() as s:
        if query.isdigit():
            u = (await s.execute(select(User).where(User.tg_id == int(query)))).scalar_one_or_none()
            if u:
                return u
        return (
            await s.execute(select(User).where(func.lower(User.username) == query.lower()))
        ).scalar_one_or_none()


async def _user_card(u: User) -> str:
    async with get_session() as s:
        bots = await s.scalar(select(func.count(ChildBot.id)).where(ChildBot.owner_id == u.id))
        refs = await s.scalar(select(func.count(User.id)).where(User.referred_by == u.id))
    block = "🚫 <b>BLOKLANGAN</b>\n" if u.is_blocked else ""
    return (
        f"👤 <b>{u.full_name or '—'}</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"{block}"
        f"├ 🆔 <code>{u.tg_id}</code>\n"
        f"├ 🔗 @{u.username or '—'}\n"
        f"├ 💰 Balans: <b>{u.balance:,.0f}</b> so'm\n"
        f"├ 🤖 Botlar: <b>{bots or 0}</b>\n"
        f"├ 👥 Takliflar: <b>{refs or 0}</b>\n"
        f"└ {'✅ tasdiqlangan' if u.is_verified else '🕓 tasdiqlanmagan'}"
    ).replace(",", " ")


def _user_kb(u: User) -> InlineKeyboardMarkup:
    ban_btn = (
        InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm:unban:{u.id}", style="success")
        if u.is_blocked
        else InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:ban:{u.id}", style="danger")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Balans", callback_data=f"adm:uadd:{u.id}", style="success"),
                InlineKeyboardButton(text="➖ Balans", callback_data=f"adm:uded:{u.id}", style="danger"),
            ],
            [InlineKeyboardButton(text="🤖 Botlari", callback_data=f"adm:ubots:{u.id}")],
            [ban_btn],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")],
        ]
    )


@router.callback_query(F.data == "adm:users")
async def users_menu(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminUser.waiting_query)
    async with get_session() as s:
        total = await s.scalar(select(func.count(User.id)))
        recent = (
            await s.execute(select(User).order_by(User.id.desc()).limit(8))
        ).scalars().all()
    rows = [
        [InlineKeyboardButton(text=f"👤 {u.full_name or u.tg_id}", callback_data=f"adm:user:{u.id}")]
        for u in recent
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")])
    await cq.message.edit_text(
        f"👥 <b>Userlar</b> (jami: {total or 0})\n"
        "━━━━━━━━━━━━━━━\n"
        "🔍 Qidirish uchun <b>tg_id</b> yoki <b>@username</b> yuboring,\n"
        "yoki so'nggilardan tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await cq.answer()


@router.message(AdminUser.waiting_query, F.text)
async def user_search(message: Message, state: FSMContext) -> None:
    if not _is_super(message.from_user.id):
        return
    u = await _find_user(message.text)
    if not u:
        await message.answer("❌ User topilmadi. tg_id yoki @username yuboring.")
        return
    await state.clear()
    await message.answer(await _user_card(u), reply_markup=_user_kb(u))


@router.callback_query(F.data.startswith("adm:user:"))
async def user_card(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.clear()
    uid = int(cq.data.split(":")[2])
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not u:
        await cq.answer("Topilmadi", show_alert=True)
        return
    await cq.message.edit_text(await _user_card(u), reply_markup=_user_kb(u))
    await cq.answer()


@router.callback_query(F.data.startswith("adm:uadd:"))
async def user_add_start(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminUser.waiting_add)
    await state.update_data(target=int(cq.data.split(":")[2]))
    await cq.message.answer("➕ Qancha so'm qo'shamiz? (masalan 50000)")
    await cq.answer()


@router.callback_query(F.data.startswith("adm:uded:"))
async def user_deduct_start(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminUser.waiting_deduct)
    await state.update_data(target=int(cq.data.split(":")[2]))
    await cq.message.answer("➖ Qancha so'm yechamiz? (masalan 20000)")
    await cq.answer()


async def _adjust_balance(message: Message, state: FSMContext, sign: int) -> None:
    data = await state.get_data()
    await state.clear()
    try:
        amount = Decimal(message.text.strip()) * sign
    except (InvalidOperation, AttributeError):
        await message.answer("❌ Noto'g'ri son.")
        return
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.id == data["target"]))).scalar_one_or_none()
        if not u:
            await message.answer("❌ User topilmadi.")
            return
        u.balance += amount
        if u.balance < 0:
            u.balance = Decimal(0)
        s.add(Payment(user_id=u.id, amount=abs(amount), provider="admin",
                      purpose="topup" if sign > 0 else "deduct", status="paid"))
        new_bal = u.balance
        tg_id = u.tg_id
    await message.answer(f"✅ Bajarildi. Yangi balans: <b>{new_bal:,.0f}</b> so'm".replace(",", " "))
    if sign > 0:
        try:
            await message.bot.send_message(
                tg_id, f"💰 Hisobingizga <b>{abs(amount):,.0f}</b> so'm qo'shildi!".replace(",", " ")
            )
        except Exception:  # noqa: BLE001
            pass


@router.message(AdminUser.waiting_add, F.text)
async def user_add(message: Message, state: FSMContext) -> None:
    if _is_super(message.from_user.id):
        await _adjust_balance(message, state, 1)


@router.message(AdminUser.waiting_deduct, F.text)
async def user_deduct(message: Message, state: FSMContext) -> None:
    if _is_super(message.from_user.id):
        await _adjust_balance(message, state, -1)


@router.callback_query(F.data.regexp(r"^adm:(ban|unban):"))
async def user_ban(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    parts = cq.data.split(":")
    block = parts[1] == "ban"
    uid = int(parts[2])
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        if u:
            u.is_blocked = block
    await cq.answer("🚫 Bloklandi" if block else "✅ Blokdan chiqarildi")
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.id == uid))).scalar_one()
    await cq.message.edit_text(await _user_card(u), reply_markup=_user_kb(u))


@router.callback_query(F.data.startswith("adm:ubots:"))
async def user_bots(cq: CallbackQuery) -> None:
    if not _is_super(cq.from_user.id):
        return
    uid = int(cq.data.split(":")[2])
    async with get_session() as s:
        bots = (await s.execute(select(ChildBot).where(ChildBot.owner_id == uid))).scalars().all()
    if not bots:
        await cq.answer("Bot yo'q", show_alert=True)
        return
    lines = ["🤖 <b>Userning botlari</b>\n━━━━━━━━━━━━━━━"]
    for b in bots:
        lines.append(f"• @{b.bot_username or b.id} — {b.status}")
    await cq.message.edit_text("\n".join(lines), reply_markup=_back_kb(f"adm:user:{uid}"))
    await cq.answer()


# ---- Promokodlar ----
@router.callback_query(F.data == "adm:promo")
async def promo_menu(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.clear()
    async with get_session() as s:
        promos = (await s.execute(select(PromoCode).order_by(PromoCode.id.desc()).limit(15))).scalars().all()
    lines = ["🎁 <b>Promokodlar</b>", "━━━━━━━━━━━━━━━"]
    if not promos:
        lines.append("Hozircha promokod yo'q.")
    for p in promos:
        mark = "🟢" if p.is_active else "🔴"
        lines.append(
            f"{mark} <code>{p.code}</code> — {p.amount:,.0f} so'm · {p.used_count}/{p.max_uses}".replace(",", " ")
        )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi promokod", callback_data="adm:promonew", style="success")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm:back")],
        ]
    )
    await cq.message.edit_text("\n".join(lines), reply_markup=kb)
    await cq.answer()


@router.callback_query(F.data == "adm:promonew")
async def promo_new(cq: CallbackQuery, state: FSMContext) -> None:
    if not _is_super(cq.from_user.id):
        return
    await state.set_state(AdminPromo.waiting_code)
    await cq.message.answer("🎁 Promokod nomini yuboring (masalan: BONUS50):")
    await cq.answer()


@router.message(AdminPromo.waiting_code, F.text)
async def promo_code(message: Message, state: FSMContext) -> None:
    if not _is_super(message.from_user.id):
        return
    code = message.text.strip().upper()
    async with get_session() as s:
        dup = await s.scalar(select(PromoCode.id).where(PromoCode.code == code))
    if dup:
        await message.answer("⚠️ Bu kod band. Boshqa nom yuboring.")
        return
    await state.update_data(code=code)
    await state.set_state(AdminPromo.waiting_amount)
    await message.answer("💰 Bonus miqdorini yuboring (so'm, masalan 50000):")


@router.message(AdminPromo.waiting_amount, F.text)
async def promo_amount(message: Message, state: FSMContext) -> None:
    if not _is_super(message.from_user.id):
        return
    try:
        amount = Decimal(message.text.strip())
    except InvalidOperation:
        await message.answer("❌ Noto'g'ri son.")
        return
    await state.update_data(amount=str(amount))
    await state.set_state(AdminPromo.waiting_max)
    await message.answer("👥 Necha marta ishlatilsin? (masalan 100):")


@router.message(AdminPromo.waiting_max, F.text)
async def promo_max(message: Message, state: FSMContext) -> None:
    if not _is_super(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Butun son yuboring.")
        return
    data = await state.get_data()
    await state.clear()
    async with get_session() as s:
        s.add(PromoCode(
            code=data["code"], amount=Decimal(data["amount"]),
            max_uses=int(message.text.strip()),
        ))
    await message.answer(
        f"✅ Promokod yaratildi!\n"
        f"🎁 <code>{data['code']}</code> — {Decimal(data['amount']):,.0f} so'm × {message.text.strip()}".replace(",", " ")
    )


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


@router.message(Command("give"))
async def give_cmd(message: Message, command: CommandObject) -> None:
    """/give <tg_id> <miqdor> — userga pul yuborish (super-admin)."""
    if not _is_super(message.from_user.id):
        return
    parts = (command.args or "").split()
    if len(parts) != 2 or not parts[0].isdigit():
        await message.answer("Foydalanish: <code>/give &lt;tg_id&gt; &lt;miqdor&gt;</code>")
        return
    try:
        amount = Decimal(parts[1])
    except InvalidOperation:
        await message.answer("❌ Noto'g'ri miqdor.")
        return
    async with get_session() as s:
        u = (await s.execute(select(User).where(User.tg_id == int(parts[0])))).scalar_one_or_none()
        if not u:
            await message.answer("❌ Bunday user topilmadi (u botni ishga tushirmagan).")
            return
        await top_up(s, u, amount, provider="admin")
        new_bal = u.balance
    await message.answer(
        f"✅ @{u.username or u.tg_id} ga <b>{amount:,.0f}</b> so'm yuborildi.\n"
        f"Yangi balans: <b>{new_bal:,.0f}</b> so'm".replace(",", " ")
    )
    try:
        await message.bot.send_message(
            int(parts[0]), f"💰 Hisobingizga <b>{amount:,.0f}</b> so'm qo'shildi!".replace(",", " ")
        )
    except Exception:  # noqa: BLE001
        pass
