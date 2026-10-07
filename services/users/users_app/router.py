"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from .apps.admin.router import router as admin_router
from .apps.users.router import router as users_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(users_router)
    app.include_router(admin_router)
    return app
