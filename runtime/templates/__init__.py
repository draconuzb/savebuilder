"""Shablon registri: template code → Dispatcher quruvchi funksiya."""
from __future__ import annotations

from collections.abc import Callable

from aiogram import Dispatcher

from core.storage import get_storage
from runtime.templates.kino.admin import build_admin_router
from runtime.templates.kino.router import build_user_router
from runtime.templates.media_spec import AUDIO, KINO, SERIAL, MediaSpec


def _media_dispatcher_builder(spec: MediaSpec) -> Callable[[int, int], Dispatcher]:
    """Berilgan media-spec uchun (child_bot_id, owner_tg_id) -> Dispatcher quruvchi."""

    def build(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
        dp = Dispatcher(storage=get_storage())
        dp.include_router(build_admin_router(child_bot_id, owner_tg_id, spec))
        dp.include_router(build_user_router(child_bot_id, spec))
        return dp

    return build


# template.code → builder(child_bot_id, owner_tg_id) -> Dispatcher
TEMPLATE_BUILDERS: dict[str, Callable[[int, int], Dispatcher]] = {
    "kino": _media_dispatcher_builder(KINO),
    "audio_pechat": _media_dispatcher_builder(AUDIO),
    "serial": _media_dispatcher_builder(SERIAL),
}
