"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI
from .apps.forum.router import router as forum_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(forum_router)
    return app