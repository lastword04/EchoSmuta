from fastapi import FastAPI

from .apps.admin.router import router as admin_router
from .apps.pawn_shop.router import router as pawn_shop_router
from .apps.tavern.router import router as tavern_router


def apply_routes(app: FastAPI) -> FastAPI:
    app.include_router(pawn_shop_router)
    app.include_router(tavern_router)
    app.include_router(admin_router)
    return app