"""FSM storage tanlash: REDIS_URL bo'lsa Redis, aks holda MemoryStorage.

Barcha dispatcherlar bitta umumiy storage'dan foydalanadi (kalitlar bot_id ni
o'z ichiga oladi, shuning uchun botlar orasida to'qnashuv bo'lmaydi)."""
from __future__ import annotations

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import get_settings

_storage: BaseStorage | None = None


def get_storage() -> BaseStorage:
    global _storage
    if _storage is None:
        url = get_settings().redis_url
        if url:
            from aiogram.fsm.storage.redis import RedisStorage

            _storage = RedisStorage.from_url(url)
        else:
            _storage = MemoryStorage()
    return _storage
