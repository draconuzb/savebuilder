"""Fon vazifasi: tarif muddati tugagan bola botlarni to'xtatish.

Obuna modelining yuragi — muddat tugasa bot o'chadi, egasi xabar oladi."""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from aiogram import Bot
from sqlalchemy import func, select

from core.config import get_settings
from core.constants import ChildBotStatus
from db.models import ChildBot, Payment, User
from db.session import get_session
from runtime.loader import unregister_child_bot

log = logging.getLogger(__name__)

CHECK_INTERVAL = 3600  # har soatda tekshiriladi
REPORT_HOUR_UTC = 4  # ~09:00 Toshkent — kunlik hisobot vaqti
_last_report: date | None = None


async def _daily_report(manager_bot: Bot) -> None:
    global _last_report
    now = datetime.now(timezone.utc)
    if now.hour != REPORT_HOUR_UTC or _last_report == now.date():
        return
    _last_report = now.date()
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    async with get_session() as s:
        users = await s.scalar(select(func.count(User.id)))
        bots = await s.scalar(select(func.count(ChildBot.id)))
        new_users = await s.scalar(
            select(func.count(User.id)).where(User.created_at >= day_start)
        )
        new_bots = await s.scalar(
            select(func.count(ChildBot.id)).where(ChildBot.created_at >= day_start)
        )
        rev_today = await s.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == "paid", Payment.created_at >= day_start
            )
        )
    text = (
        "📊 <b>Kunlik hisobot</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"👥 Jami userlar: <b>{users or 0}</b> (bugun +{new_users or 0})\n"
        f"🤖 Jami botlar: <b>{bots or 0}</b> (bugun +{new_bots or 0})\n"
        f"💰 Bugungi daromad: <b>{rev_today or 0:,.0f}</b> so'm".replace(",", " ")
    )
    for admin_id in get_settings().super_admin_ids:
        try:
            await manager_bot.send_message(admin_id, text)
        except Exception:  # noqa: BLE001
            pass
    log.info("Kunlik hisobot yuborildi")


async def _check_expired(manager_bot: Bot) -> None:
    now = datetime.now(timezone.utc)
    async with get_session() as s:
        rows = (
            await s.execute(
                select(ChildBot, User)
                .join(User, ChildBot.owner_id == User.id)
                .where(
                    ChildBot.status == ChildBotStatus.ACTIVE,
                    ChildBot.expires_at.is_not(None),
                    ChildBot.expires_at < now,
                )
            )
        ).all()
        expired = [
            (c.id, c.webhook_secret, c.bot_username, u.tg_id) for c, u in rows
        ]
        for c, _u in rows:
            c.status = ChildBotStatus.EXPIRED

    for child_id, secret, username, owner_tg in expired:
        await unregister_child_bot(secret)
        try:
            await manager_bot.send_message(
                owner_tg,
                f"⏰ <b>@{username}</b> botingiz tarifi tugadi va to'xtatildi.\n"
                f"«🤖 Botlarim» → tarifni uzaytiring.",
            )
        except Exception:  # noqa: BLE001
            pass
        log.info("Bola bot muddati tugadi va to'xtatildi: child=%s", child_id)

    if expired:
        log.info("%s ta bola bot muddati tugadi", len(expired))


async def scheduler_loop(manager_bot: Bot) -> None:
    log.info("Scheduler ishga tushdi (har %s s)", CHECK_INTERVAL)
    while True:
        try:
            await _check_expired(manager_bot)
            await _daily_report(manager_bot)
        except Exception as e:  # noqa: BLE001
            log.exception("Scheduler xatosi: %s", e)
        await asyncio.sleep(CHECK_INTERVAL)
