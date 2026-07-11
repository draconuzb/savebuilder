"""Manager bot middleware'lari."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from sqlalchemy import select

from db.models import User
from db.session import get_session


class BlockMiddleware(BaseMiddleware):
    """Bloklangan userlarning barcha so'rovlarini to'xtatadi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            async with get_session() as s:
                blocked = await s.scalar(
                    select(User.is_blocked).where(User.tg_id == user.id)
                )
            if blocked:
                obj = event.message or event.callback_query
                try:
                    if isinstance(obj, CallbackQuery):
                        await obj.answer("🚫 Siz bloklangansiz.", show_alert=True)
                    elif isinstance(obj, Message):
                        await obj.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
                except Exception:  # noqa: BLE001
                    pass
                return None
        return await handler(event, data)
