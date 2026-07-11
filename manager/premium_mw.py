"""Chiquvchi so'rov middleware'i — manager bot har bir xabar matnini premium emoji qiladi.

Bu har handlerni qo'lda o'rashdan qutqaradi: barcha tugmalar ichidagi hamma
ekran avtomatik animatsiyali custom emoji oladi (bot egasi Premium bo'lsa)."""
from __future__ import annotations

from typing import Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from manager.texts import premiumize


class PremiumEmojiMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Any:
        updates: dict[str, str] = {}
        text = getattr(method, "text", None)
        if isinstance(text, str) and text:
            updates["text"] = premiumize(text)
        caption = getattr(method, "caption", None)
        if isinstance(caption, str) and caption:
            updates["caption"] = premiumize(caption)
        if updates:
            method = method.model_copy(update=updates)
        return await make_request(bot, method)
