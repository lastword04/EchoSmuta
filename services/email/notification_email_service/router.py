"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI
from .apps.emails.router import router as email_router


def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(email_router)
    
    return app