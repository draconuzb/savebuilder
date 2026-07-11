"""Shablon registri: template code → Dispatcher quruvchi funksiya."""
from __future__ import annotations

from collections.abc import Callable

from aiogram import Dispatcher

from core.storage import get_storage
from runtime.templates.anon.router import build_anon_router
from runtime.templates.finance.router import build_finance_router
from runtime.templates.group.router import build_group_router
from runtime.templates.kino.admin import build_admin_router
from runtime.templates.poll.router import build_poll_router
from runtime.templates.kino.router import build_user_router
from runtime.templates.media_spec import AUDIO, KINO, SERIAL, MediaSpec


def _video(noun: str, emoji: str) -> MediaSpec:
    return MediaSpec(media_type="video", emoji=emoji, noun=noun, ask_word="video")


def _media_dispatcher_builder(spec: MediaSpec) -> Callable[[int, int], Dispatcher]:
    """Berilgan media-spec uchun (child_bot_id, owner_tg_id) -> Dispatcher quruvchi."""

    def build(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
        dp = Dispatcher(storage=get_storage())
        dp.include_router(build_admin_router(child_bot_id, owner_tg_id, spec))
        dp.include_router(build_user_router(child_bot_id, spec))
        return dp

    return build


def _anon_dispatcher(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
    dp = Dispatcher(storage=get_storage())
    dp.include_router(build_anon_router(child_bot_id, owner_tg_id))
    return dp


def _group_dispatcher(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
    dp = Dispatcher(storage=get_storage())
    dp.include_router(build_group_router(child_bot_id, owner_tg_id))
    return dp


def _finance_dispatcher(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
    dp = Dispatcher(storage=get_storage())
    dp.include_router(build_finance_router(child_bot_id, owner_tg_id))
    return dp


def _poll_dispatcher_builder(is_quiz: bool) -> Callable[[int, int], Dispatcher]:
    def build(child_bot_id: int, owner_tg_id: int) -> Dispatcher:
        dp = Dispatcher(storage=get_storage())
        dp.include_router(build_poll_router(child_bot_id, owner_tg_id, is_quiz))
        return dp

    return build


# template.code → builder(child_bot_id, owner_tg_id) -> Dispatcher
TEMPLATE_BUILDERS: dict[str, Callable[[int, int], Dispatcher]] = {
    "kino": _media_dispatcher_builder(KINO),
    "audio_pechat": _media_dispatcher_builder(AUDIO),
    "serial": _media_dispatcher_builder(SERIAL),
    "kino_pro": _media_dispatcher_builder(_video("Kino", "🎬")),
    "video_bot": _media_dispatcher_builder(_video("Video", "📹")),
    "drama": _media_dispatcher_builder(_video("Drama", "🎭")),
    "anon": _anon_dispatcher,
    "group_welcome": _group_dispatcher,
    "poll": _poll_dispatcher_builder(is_quiz=False),
    "quiz": _poll_dispatcher_builder(is_quiz=True),
    "currency": _finance_dispatcher,
}
