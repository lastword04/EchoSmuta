"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from .apps.admin.router import router as admin_router
from .apps.items.routes import router as items_router
from .apps.resources.router import internal_router as internal_resources_router
from .apps.resources.router import router as resources_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(internal_resources_router)
    app.include_router(resources_router)
    app.include_router(items_router)
    app.include_router(admin_router)

    return app
