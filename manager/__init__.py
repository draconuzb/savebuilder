"""Manager bot: Bot + Dispatcher qurish."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import get_settings
from core.storage import get_storage


def build_manager_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.manager_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_manager_dispatcher() -> Dispatcher:
    from manager.handlers import build_manager_router
    from manager.middlewares import BlockMiddleware

    dp = Dispatcher(storage=get_storage())
    dp.update.outer_middleware(BlockMiddleware())
    dp.include_router(build_manager_router())
    return dp
