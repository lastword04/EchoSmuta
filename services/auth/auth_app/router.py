"""
Основной модуль для роутов приложения.
"""

from fastapi import FastAPI

from .apps.admin.router import router as admin_router
from .apps.auth.router import router as auth_router
from .apps.visits.router import router as visit_router

def apply_routes(app: FastAPI) -> FastAPI:
    """
    Применяем роуты приложения.
    """

    app.include_router(auth_router)
    app.include_router(visit_router)
    app.include_router(admin_router)
    return app