"""Manager handler routerlarini yig'ish."""
from aiogram import Router

from manager.handlers import create, menu, start


def build_manager_router() -> Router:
    router = Router(name="manager-root")
    router.include_router(start.router)
    router.include_router(create.router)
    router.include_router(menu.router)
    return router
