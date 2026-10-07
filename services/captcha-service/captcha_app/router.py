"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from .apps.captcha.router import router as captcha_router

def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(captcha_router)
    return app