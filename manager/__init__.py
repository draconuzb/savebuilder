"""Manager bot: Bot + Dispatcher qurish."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from core.config import get_settings


def build_manager_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.manager_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_manager_dispatcher() -> Dispatcher:
    from manager.handlers import build_manager_router

    settings = get_settings()
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    dp.include_router(build_manager_router())
    return dp
