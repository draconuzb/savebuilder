"""Bola bot shablonlari uchun umumiy yordamchilar."""
from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy import select

from db.models import ForceChannel
from db.session import get_session

log = logging.getLogger(__name__)


async def child_is_subscribed(bot: Bot, child_bot_id: int, tg_id: int) -> bool:
    """Bola bot majburiy obuna kanallariga a'zolikni tekshirish."""
    async with get_session() as s:
        res = await s.execute(
            select(ForceChannel).where(ForceChannel.child_bot_id == child_bot_id)
        )
        channels = res.scalars().all()
    if not channels:
        return True
    for ch in channels:
        target = ch.channel_id or (f"@{ch.channel_username.lstrip('@')}" if ch.channel_username else None)
        if target is None:
            continue
        try:
            member = await bot.get_chat_member(target, tg_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception as e:  # noqa: BLE001
            log.warning("child force-sub tekshiruv xato: %s", e)
    return True
