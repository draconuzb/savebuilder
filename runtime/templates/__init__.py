"""Shablon registri: template code → Dispatcher quruvchi funksiya."""
from __future__ import annotations

from collections.abc import Callable

from aiogram import Dispatcher

from core.storage import get_storage
from runtime.templates.kino.admin import build_admin_router
from runtime.templates.kino.router import build_user_router


def _build_kino_dispatcher(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
    dp = Dispatcher(storage=get_storage())
    # Admin router (egaga) birinchi — FSM va /admin ustuvor
    dp.include_router(build_admin_router(child_bot_id, owner_tg_id))
    dp.include_router(build_user_router(child_bot_id))
    return dp


# template.code → builder(child_bot_id, owner_tg_id) -> Dispatcher
TEMPLATE_BUILDERS: dict[str, Callable[[int, int], Dispatcher]] = {
    "kino": _build_kino_dispatcher,
}
