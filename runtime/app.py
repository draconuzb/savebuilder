"""FastAPI webhook multiplekser: manager + barcha bola botlar bitta serverda."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from core.config import get_settings
from core.logging import setup_logging
from manager import build_manager_bot, build_manager_dispatcher
from runtime import registry
from runtime.loader import load_all_active

WEBAPP_HTML = (Path(__file__).resolve().parent.parent / "webapp" / "index.html").read_text(
    encoding="utf-8"
)

setup_logging()
log = logging.getLogger(__name__)
settings = get_settings()

manager_bot = build_manager_bot()
manager_dp = build_manager_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bot buyruqlari menyusi
    from aiogram.types import BotCommand

    await manager_bot.set_my_commands(
        [
            BotCommand(command="start", description="🏠 Botni ishga tushirish"),
            BotCommand(command="help", description="📖 Yordam"),
        ]
    )
    try:
        await manager_bot.set_my_description(
            "🤖 Kod yozmasdan o'z Telegram botingizni yarating!\n"
            "Kino, Serial, Audio botlar — tez, oson, professional."
        )
        await manager_bot.set_my_short_description(
            "Kod yozmasdan Telegram bot yaratish platformasi 🚀"
        )
    except Exception as e:  # noqa: BLE001
        log.warning("Bot tavsifini o'rnatishda xato: %s", e)
    # Manager webhook
    await manager_bot.set_webhook(settings.manager_webhook_url, drop_pending_updates=True)
    log.info("Manager webhook o'rnatildi: %s", settings.manager_webhook_url)
    # Aktiv bola botlarni yuklash
    n = await load_all_active()
    log.info("%s ta aktiv bola bot yuklandi", n)
    # Muddat nazorati (fon vazifasi)
    import asyncio

    from runtime.scheduler import scheduler_loop

    scheduler_task = asyncio.create_task(scheduler_loop(manager_bot))
    yield
    # Yopilishda
    scheduler_task.cancel()
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


@app.get("/webapp", response_class=HTMLResponse)
async def webapp_page() -> HTMLResponse:
    return HTMLResponse(WEBAPP_HTML)


@app.post("/webapp/verify")
async def webapp_verify(request: Request) -> JSONResponse:
    """Mini App initData'ni tekshiradi, userni verified qiladi va menyuni yuboradi."""
    from sqlalchemy import select

    from db.models import User
    from db.session import get_session
    from manager.keyboards import MAIN_MENU
    from manager.texts import WELCOME
    from security.antibot import validate_init_data

    body = await request.json()
    init_data = body.get("init_data", "")
    tg_user = validate_init_data(init_data, settings.manager_bot_token)
    if not tg_user:
        return JSONResponse({"ok": False, "error": "Tekshiruv muvaffaqiyatsiz"}, status_code=400)

    tg_id = tg_user.get("id")
    async with get_session() as s:
        user = (
            await s.execute(select(User).where(User.tg_id == tg_id))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                tg_id=tg_id,
                username=tg_user.get("username"),
                full_name=" ".join(
                    x for x in [tg_user.get("first_name"), tg_user.get("last_name")] if x
                ),
                is_verified=True,
            )
            s.add(user)
        else:
            user.is_verified = True

    try:
        await manager_bot.send_message(tg_id, WELCOME, reply_markup=MAIN_MENU)
    except Exception as e:  # noqa: BLE001
        log.warning("Menyu yuborishda xato: %s", e)

    return JSONResponse({"ok": True})


@app.post("/wh/child/{secret}")
async def child_webhook(secret: str, request: Request) -> Response:
    rb = registry.get(secret)
    if rb is None:
        log.warning("Noma'lum bola bot secret: %s", secret[:6])
        return Response(status_code=200)  # Telegram qayta yubormasin
    update = Update.model_validate(await request.json(), context={"bot": rb.bot})
    await rb.dp.feed_update(rb.bot, update)
    return Response(status_code=200)
