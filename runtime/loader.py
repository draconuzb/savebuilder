"""Bola botlarni yuklash: DB dan o'qib, Bot+Dispatcher qurib, webhook o'rnatish."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select

from core.config import get_settings
from core.constants import ChildBotStatus
from db.models import ChildBot, Template, User
from db.session import get_session
from runtime import registry
from runtime.templates import TEMPLATE_BUILDERS
from security.crypto import decrypt_token

log = logging.getLogger(__name__)


async def register_child_bot(child_id: int) -> None:
    """Bitta bola botni ishga tushirish (webhook + registry)."""
    settings = get_settings()
    async with get_session() as s:
        child = (
            await s.execute(select(ChildBot).where(ChildBot.id == child_id))
        ).scalar_one_or_none()
        if child is None:
            raise ValueError(f"ChildBot {child_id} topilmadi")
        template = (
            await s.execute(select(Template).where(Template.id == child.template_id))
        ).scalar_one()
        owner = (
            await s.execute(select(User).where(User.id == child.owner_id))
        ).scalar_one()
        token = decrypt_token(child.token_enc)
        secret = child.webhook_secret
        template_code = template.code
        owner_tg_id = owner.tg_id

    builder = TEMPLATE_BUILDERS.get(template_code)
    if builder is None:
        raise ValueError(f"'{template_code}' shabloni uchun builder yo'q")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = builder(child_id, owner_tg_id)

    webhook_url = settings.child_webhook_url(secret)
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    registry.add(registry.RunningBot(child_id=child_id, secret=secret, bot=bot, dp=dp))
    log.info("Bola bot ishga tushdi: child=%s secret=%s", child_id, secret[:6])


async def unregister_child_bot(secret: str) -> None:
    rb = registry.remove(secret)
    if rb:
        try:
            await rb.bot.delete_webhook()
        finally:
            await rb.bot.session.close()


async def load_all_active() -> int:
    """Startupda barcha aktiv bola botlarni yuklash."""
    async with get_session() as s:
        res = await s.execute(
            select(ChildBot.id).where(ChildBot.status == ChildBotStatus.ACTIVE)
        )
        ids = [row[0] for row in res.all()]
    loaded = 0
    for cid in ids:
        try:
            await register_child_bot(cid)
            loaded += 1
        except Exception as e:  # noqa: BLE001
            log.exception("Bola bot yuklashda xato (child=%s): %s", cid, e)
    return loaded
