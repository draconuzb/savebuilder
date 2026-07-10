"""Ishlab turgan bola botlar registri (xotirada)."""
from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher


@dataclass
class RunningBot:
    child_id: int
    secret: str
    bot: Bot
    dp: Dispatcher


# webhook_secret → RunningBot
_by_secret: dict[str, RunningBot] = {}


def add(rb: RunningBot) -> None:
    _by_secret[rb.secret] = rb


def get(secret: str) -> RunningBot | None:
    return _by_secret.get(secret)


def remove(secret: str) -> RunningBot | None:
    return _by_secret.pop(secret, None)


def all_bots() -> list[RunningBot]:
    return list(_by_secret.values())
