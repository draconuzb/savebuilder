"""Lokal test uchun POLLING rejimi (domensiz).

Manager bot + barcha aktiv bola botlarni long-polling orqali ishga tushiradi.
Webhook o'rnatishga hojat yo'q — HTTPS domen shart emas.

Ishlatish:  python -m scripts.run_polling
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from core.constants import ChildBotStatus
from core.logging import setup_logging
from db.models import ChildBot
from db.session import get_session
from manager import build_manager_bot, build_manager_dispatcher
from runtime.loader import build_child

setup_logging()
log = logging.getLogger("run_polling")


async def _active_child_ids() -> list[int]:
    async with get_session() as s:
        res = await s.execute(
            select(ChildBot.id).where(ChildBot.status == ChildBotStatus.ACTIVE)
        )
        return [r[0] for r in res.all()]


async def main() -> None:
    tasks: list[asyncio.Task] = []
    bots = []

    # Manager
    manager_bot = build_manager_bot()
    manager_dp = build_manager_dispatcher()
    await manager_bot.delete_webhook(drop_pending_updates=True)
    bots.append(manager_bot)
    tasks.append(asyncio.create_task(manager_dp.start_polling(manager_bot)))
    log.info("Manager bot polling boshlandi")

    # Bola botlar
    for cid in await _active_child_ids():
        try:
            bot, dp, _ = await build_child(cid)
            await bot.delete_webhook(drop_pending_updates=True)
            bots.append(bot)
            tasks.append(asyncio.create_task(dp.start_polling(bot)))
            log.info("Bola bot polling boshlandi: child=%s", cid)
        except Exception as e:  # noqa: BLE001
            log.exception("Bola bot polling xato (child=%s): %s", cid, e)

    try:
        await asyncio.gather(*tasks)
    finally:
        for b in bots:
            await b.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("To'xtatildi")
