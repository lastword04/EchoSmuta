"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from .apps.admin.router import router as admin_router
from .apps.characters.routes import router as characters_router
from .apps.exchanges.router import router as exchanges_router
from .apps.notebook.router import router as notebook_router
from .apps.panels.router import router as panels_router
from .apps.stats.router import router as stats_router
from .apps.rest.router import router as rest_router, houses_router
from .apps.characters.routes import websocket_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(characters_router)
    app.include_router(exchanges_router)
    app.include_router(notebook_router)
    app.include_router(panels_router)
    app.include_router(stats_router)
    app.include_router(websocket_router)
    app.include_router(rest_router)
    app.include_router(houses_router)
    app.include_router(admin_router)
    return app