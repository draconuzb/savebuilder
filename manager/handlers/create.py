"""Bot yaratish oqimi: kategoriya → shablon → token → tarif → bola bot."""
from __future__ import annotations

import logging
import secrets

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from core.constants import CATEGORY_TITLES, ChildBotStatus
from db.models import ChildBot, Tariff, Template, User
from db.session import get_session
from manager import texts
from manager.keyboards import (
    MAIN_MENU,
    categories_kb,
    tariffs_kb,
    template_page_kb,
    templates_kb,
)
from manager.states import CreateBot

router = Router(name="manager-create")
log = logging.getLogger(__name__)


@router.message(F.text == "➕ Bot yaratish")
async def start_create(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateBot.choosing_category)
    await message.answer(texts.CHOOSE_CATEGORY, reply_markup=categories_kb())


@router.callback_query(F.data == "create:cancel")
async def cancel(cq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cq.message.edit_text("❌ Bekor qilindi.")
    await cq.message.answer("Asosiy menyu:", reply_markup=MAIN_MENU)
    await cq.answer()


@router.callback_query(F.data.startswith("cat:"))
async def choose_category(cq: CallbackQuery, state: FSMContext) -> None:
    category = cq.data.split(":", 1)[1]
    async with get_session() as s:
        res = await s.execute(
            select(Template.code, Template.title).where(
                Template.category == category, Template.is_active.is_(True)
            )
        )
        tpls = res.all()
    if not tpls:
        await cq.answer("Bu kategoriyada hali shablon yo'q.", show_alert=True)
        return
    await state.set_state(CreateBot.choosing_template)
    await cq.message.edit_text(
        f"{CATEGORY_TITLES.get(category, '')}\n\n{texts.CHOOSE_TEMPLATE}",
        reply_markup=templates_kb([(c, t) for c, t in tpls]),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("tpl:"))
async def show_template(cq: CallbackQuery) -> None:
    code = cq.data.split(":", 1)[1]
    async with get_session() as s:
        res = await s.execute(select(Template).where(Template.code == code))
        tpl = res.scalar_one_or_none()
    if not tpl:
        await cq.answer("Shablon topilmadi.", show_alert=True)
        return
    from manager.texts import premiumize

    text = premiumize(
        f"{tpl.title}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{tpl.description or ''}\n\n"
        f"💰 Ochish narxi: <b>{tpl.create_price:,.0f}</b> so'm\n"
        f"💳 Oylik to'lov: <i>tarifga qarab</i>\n"
        f"🤖 Namuna: {tpl.example_username or '—'}\n"
        f"🎫 Versiya: {tpl.version}".replace(",", " ")
    )
    await cq.message.edit_text(text, reply_markup=template_page_kb(code))
    await cq.answer()


@router.callback_query(F.data.startswith("tpltariffs:"))
async def show_tariffs_info(cq: CallbackQuery) -> None:
    async with get_session() as s:
        res = await s.execute(select(Tariff).where(Tariff.is_active.is_(True)))
        tariffs = res.scalars().all()
    from manager.texts import premiumize

    lines = ["🎟 <b>Tariflar ro'yxati</b>", "━━━━━━━━━━━━━━━"]
    for t in tariffs:
        per_day = float(t.price) / t.duration_days if t.duration_days else 0
        lines.append(
            f"⚡️ <b>{t.name}</b> · {t.speed_x}x tezlik\n"
            f"   ├ 📅 {t.duration_days} kun\n"
            f"   └ 💰 <b>{t.price:,.0f}</b> so'm  <i>({per_day:,.0f}/kun)</i>"
        )
    await cq.answer()
    await cq.message.answer(premiumize("\n".join(lines)).replace(",", " "))


@router.callback_query(F.data.startswith("tplcreate:"))
async def ask_token(cq: CallbackQuery, state: FSMContext) -> None:
    code = cq.data.split(":", 1)[1]
    async with get_session() as s:
        res = await s.execute(select(Template).where(Template.code == code))
        tpl = res.scalar_one_or_none()
    if not tpl:
        await cq.answer("Shablon topilmadi.", show_alert=True)
        return
    await state.update_data(template_code=code, template_id=tpl.id)
    await state.set_state(CreateBot.waiting_token)
    await cq.message.answer(texts.ASK_TOKEN.format(template=tpl.title))
    await cq.answer()


@router.message(CreateBot.waiting_token, F.text)
async def receive_token(message: Message, state: FSMContext) -> None:
    token = message.text.strip()
    # Tokenni tekshirish (getMe)
    test_bot = None
    try:
        test_bot = Bot(token=token)
        me = await test_bot.get_me()
    except Exception as e:  # noqa: BLE001  (TokenValidationError, Unauthorized, network...)
        log.info("Token validatsiya xato: %s", e)
        await message.answer(texts.TOKEN_INVALID)
        if test_bot is not None:
            await test_bot.session.close()
        return
    await test_bot.session.close()

    await state.update_data(
        token=token, bot_username=me.username, bot_tg_id=me.id
    )
    async with get_session() as s:
        res = await s.execute(select(Tariff).where(Tariff.is_active.is_(True)))
        tariffs = res.scalars().all()
    await message.answer(
        texts.TOKEN_OK.format(username=me.username),
        reply_markup=tariffs_kb([(t.id, t.name, t.price) for t in tariffs]),
    )
    await state.set_state(CreateBot.choosing_tariff)


@router.callback_query(CreateBot.choosing_tariff, F.data.startswith("tariff:"))
async def choose_tariff(cq: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    tariff_id = int(cq.data.split(":", 1)[1])
    data = await state.get_data()

    from security.crypto import encrypt_token  # lokal import (sikl oldini olish)
    from manager.services.billing import InsufficientBalance, charge, tariff_expiry

    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == cq.from_user.id))
        ).scalar_one_or_none()
        if user is None:
            await cq.answer("Iltimos /start bosing.", show_alert=True)
            return

        template = (
            await s.execute(select(Template).where(Template.id == data["template_id"]))
        ).scalar_one()
        tariff = (
            await s.execute(select(Tariff).where(Tariff.id == tariff_id))
        ).scalar_one()

        total = template.create_price + tariff.price
        try:
            await charge(
                s, user, total, purpose="create_bot", child_bot_id=None
            )
        except InsufficientBalance as e:
            await cq.answer()
            await cq.message.answer(
                f"❌ Balans yetarli emas.\n"
                f"Kerak: <b>{e.need:,.0f}</b> so'm · Bor: <b>{e.have:,.0f}</b> so'm\n"
                f"«💳 Pul kiritish» orqali balansni to'ldiring."
            )
            await state.clear()
            return

        secret = secrets.token_urlsafe(24)
        expires = tariff_expiry(tariff.duration_days)
        child = ChildBot(
            owner_id=user.id,
            template_id=data["template_id"],
            token_enc=encrypt_token(data["token"]),
            bot_username=data["bot_username"],
            bot_tg_id=data["bot_tg_id"],
            webhook_secret=secret,
            tariff_id=tariff_id,
            status=ChildBotStatus.ACTIVE,
            expires_at=expires,
            config={},
        )
        s.add(child)
        await s.flush()
        child_id = child.id
        tariff_name = tariff.name
        new_balance = user.balance

    # Bola botga webhook o'rnatish (runtime orqali)
    try:
        from runtime.loader import register_child_bot

        await register_child_bot(child_id)
        status_line = "🟢 <b>Bot jonli ishga tushdi!</b>"
    except Exception as e:  # noqa: BLE001
        log.exception("register_child_bot xato: %s", e)
        status_line = "⚠️ Bot yaratildi, lekin ishga tushirishda xato. Admin tekshiradi."

    from manager.texts import premiumize

    await state.clear()
    username = data["bot_username"]
    await cq.message.edit_text(
        premiumize(
            "🎉 <b>Tabriklaymiz — bot tayyor!</b>\n"
            "━━━━━━━━━━━━━━━\n"
            f"🤖 <b>@{username}</b>\n"
            f"🎟 Tarif: <b>{tariff_name}</b>\n"
            f"📅 Amal qiladi: <b>{expires.strftime('%Y-%m-%d')}</b> gacha\n"
            f"💰 Qolgan balans: <b>{new_balance:,.0f}</b> so'm\n\n"
            f"{status_line}\n\n"
            f"👉 <a href='https://t.me/{username}'>Botni ochish</a> · "
            f"«🤖 Botlarim» orqali boshqaring".replace(",", " ")
        ),
        disable_web_page_preview=True,
    )
    await cq.message.answer("🏠 Asosiy menyu:", reply_markup=MAIN_MENU)
    await cq.answer("🎉 Bot yaratildi!")
