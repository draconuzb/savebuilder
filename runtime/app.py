"""FastAPI webhook multiplekser: manager + barcha bola botlar bitta serverda."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request, Response

from core.config import get_settings
from core.logging import setup_logging
from manager import build_manager_bot, build_manager_dispatcher
from runtime import registry
from runtime.loader import load_all_active

setup_logging()
log = logging.getLogger(__name__)
settings = get_settings()

manager_bot = build_manager_bot()
manager_dp = build_manager_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Manager webhook
    await manager_bot.set_webhook(settings.manager_webhook_url, drop_pending_updates=True)
    log.info("Manager webhook o'rnatildi: %s", settings.manager_webhook_url)
    # Aktiv bola botlarni yuklash
    n = await load_all_active()
    log.info("%s ta aktiv bola bot yuklandi", n)
    yield
    # Yopilishda
    await manager_bot.session.close()
    for rb in registry.all_bots():
        await rb.bot.session.close()


app = FastAPI(title="SaveBuilder Clone", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "child_bots": len(registry.all_bots())}


@app.post(settings.manager_webhook_path)
async def manager_webhook(request: Request) -> Response:
    update = Update.model_validate(await request.json(), context={"bot": manager_bot})
    await manager_dp.feed_update(manager_bot, update)
    return Response(status_code=200)


@app.post("/wh/child/{secret}")
async def child_webhook(secret: str, request: Request) -> Response:
    rb = registry.get(secret)
    if rb is None:
        log.warning("Noma'lum bola bot secret: %s", secret[:6])
        return Response(status_code=200)  # Telegram qayta yubormasin
    update = Update.model_validate(await request.json(), context={"bot": rb.bot})
    await rb.dp.feed_update(rb.bot, update)
    return Response(status_code=200)
