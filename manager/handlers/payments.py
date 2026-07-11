"""«💳 Pul kiritish» — Telegram Stars orqali balans to'ldirish + referal bonus."""
from __future__ import annotations

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy import select

from db.models import ReferralReward, User
from db.session import get_session
from manager.services.billing import top_up
from payments.stars import STAR_PACKAGES, parse_payload, send_topup_invoice

router = Router(name="manager-payments")
log = logging.getLogger(__name__)

REFERRAL_PERCENT = 10  # referal bonus foizi (to'ldirilgan summadan)


def _packages_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{som:,} so'm  —  {stars} ⭐".replace(",", " "),
                callback_data=f"topup:{stars}:{som}",
                style="primary",
            )
        ]
        for stars, som in STAR_PACKAGES
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "💳 Pul kiritish")
async def topup_menu(message: Message) -> None:
    from manager.texts import premiumize

    await message.answer(
        premiumize(
            "💰 <b>Pul kiritish</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "Balansni <b>Telegram Stars</b> ⭐️ orqali to'ldiring — "
            "tez, komissiyasiz va bevosita Telegram ichida.\n\n"
            "Paketni tanlang:"
        ),
        reply_markup=_packages_kb(),
    )


@router.callback_query(F.data.startswith("topup:"))
async def topup_invoice(cq: CallbackQuery) -> None:
    _, stars_s, som_s = cq.data.split(":")
    await send_topup_invoice(cq.bot, cq.from_user.id, int(stars_s), int(som_s))
    await cq.answer("Invoice yuborildi ⭐")


@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery) -> None:
    # Stars to'lovi — har doim tasdiqlaymiz (payload valid bo'lsa)
    if parse_payload(pcq.invoice_payload) is None:
        await pcq.answer(ok=False, error_message="Noto'g'ri to'lov.")
        return
    await pcq.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(message: Message) -> None:
    sp = message.successful_payment
    som = parse_payload(sp.invoice_payload)
    if som is None:
        return
    amount = Decimal(som)

    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == message.from_user.id))
        ).scalar_one_or_none()
        if user is None:
            return
        await top_up(s, user, amount, provider="stars")
        new_balance = user.balance

        # Referal bonus — taklif qilgan userga foiz
        bonus_line = ""
        if user.referred_by:
            referrer = (
                await s.execute(select(User).where(User.id == user.referred_by))
            ).scalar_one_or_none()
            if referrer:
                bonus = amount * REFERRAL_PERCENT // 100
                if bonus > 0:
                    referrer.balance += bonus
                    s.add(
                        ReferralReward(
                            referrer_id=referrer.id,
                            referred_id=user.id,
                            amount=bonus,
                        )
                    )
                    # Taklif qilganга xabar (best-effort)
                    try:
                        await message.bot.send_message(
                            referrer.tg_id,
                            f"💎 Referal bonus: <b>+{bonus:,.0f}</b> so'm\n"
                            f"Do'stingiz balans to'ldirdi.".replace(",", " "),
                        )
                    except Exception:  # noqa: BLE001
                        pass

    from manager.texts import premiumize

    await message.answer(
        premiumize(
            "🎉 <b>To'lov qabul qilindi!</b>\n"
            "━━━━━━━━━━━━━━━\n"
            f"⭐️ {sp.total_amount} Stars  →  <b>+{som:,}</b> so'm\n"
            f"💰 Yangi balans: <b>{new_balance:,.0f}</b> so'm".replace(",", " ")
        )
        + bonus_line
    )
