"""Shablon registri: template code → Dispatcher quruvchi funksiya."""
from __future__ import annotations

from collections.abc import Callable

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from core.config import get_settings
from runtime.templates.kino.router import build_kino_router


def _build_kino_dispatcher(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
    storage = RedisStorage.from_url(get_settings().redis_url)
    dp = Dispatcher(storage=storage)
    dp.include_router(build_kino_router(child_bot_id, owner_tg_id))
    return dp


# template.code → builder(child_bot_id, owner_tg_id) -> Dispatcher
TEMPLATE_BUILDERS: dict[str, Callable[[int, int], Dispatcher]] = {
    "kino": _build_kino_dispatcher,
}
