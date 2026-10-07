"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI
from .apps.mails.router import router as mails_router
from .apps.messages.router import router as messages_router
from .apps.categories.router import router as categories_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """
    app.include_router(mails_router)
    app.include_router(messages_router)
    app.include_router(categories_router)

    return app