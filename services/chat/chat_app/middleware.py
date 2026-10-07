"""
Основной модуль для middleware приложения.
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .settings import settings
from .core.redis import get_redis_client
from shared.middleware.ban_check import BanCheckMiddleware
from shared.services.tokens_utils import DecodeAccessTokenService


def apply_middleware(app: FastAPI) -> FastAPI:
    """
    Применяем middleware.
    """
    # Проверка бана персонажа
    decode_service = DecodeAccessTokenService(
        secret_key=settings.user_access_token.secret_key,
        algorithm=settings.user_access_token.algorithm
    )
    app.add_middleware(
        BanCheckMiddleware,
        redis_client=get_redis_client(),
        decode_service=decode_service
    )

    # CORS (добавляем последним — выполняется первым)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    return app