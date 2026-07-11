"""Manager handler routerlarini yig'ish."""
from aiogram import Router

from manager.handlers import admin, create, menu, my_bots, payments, promo, start


def build_manager_router() -> Router:
    router = Router(name="manager-root")
    router.include_router(start.router)
    router.include_router(admin.router)
    router.include_router(promo.router)
    router.include_router(payments.router)
    router.include_router(create.router)
    router.include_router(my_bots.router)
    router.include_router(menu.router)
    return router
