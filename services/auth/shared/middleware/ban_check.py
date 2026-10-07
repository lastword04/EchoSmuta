"""
ASGI middleware для проверки бана персонажей.

Использует pure ASGI вместо BaseHTTPMiddleware,
чтобы корректно работать с WebSocket соединениями.
"""
from fastapi import status
import redis.asyncio as redis
import logging
import json
from jose import jwt

logger = logging.getLogger(__name__)


class BanCheckMiddleware:
    """
    Проверяет Redis ключ banned_character:{character_id} на каждый запрос.
    Если персонаж в blacklist — возвращает 403.

    Для WebSocket соединений — пропускает без проверки
    (WebSocket endpoint сам делает авторизацию).
    """

    def __init__(
        self, 
        app, 
        redis_client: redis.Redis, 
        decode_service=None,
        secret_key: str = None,
        algorithm: str = None
    ):
        self.app = app
        self.redis = redis_client
        self.decode_service = decode_service
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def __call__(self, scope, receive, send):
        # === WebSocket: пропускаем без проверки ===
        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return

        # === Не HTTP запросы (lifespan и т.п.): пропускаем ===
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # === HTTP запросы: проверяем бан ===
        path = scope.get("path", "")

        # Пропускаем внутренние сервисные запросы и auth endpoints
        if '/internal/' in path or path.startswith('/api/auth/'):
            await self.app(scope, receive, send)
            return

        # Если нет secret_key — используем старый путь через decode_service
        if not self.secret_key or not self.algorithm:
            await self._legacy_path(scope, receive, send, path)
            return

        # Ищем токен: сначала в Authorization header, потом в cookie
        token = None
        headers = dict(scope.get("headers", []))

        auth_header = headers.get(b"authorization")
        if auth_header:
            auth_header_str = auth_header.decode("utf-8")
            if auth_header_str.startswith("Bearer "):
                token = auth_header_str.split(" ")[1]

        if not token:
            cookie_header = headers.get(b"cookie")
            if cookie_header:
                cookie_str = cookie_header.decode("utf-8")
                cookies = dict(item.split("=", 1) for item in cookie_str.split("; ") if "=" in item)
                token = cookies.get("access_token")

        if not token:
            await self.app(scope, receive, send)
            return

        try:
            # Декодируем токен БЕЗ проверки audience
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False}
            )
            
            # Проверяем тип токена
            has_audience = "aud" in payload
            
            if has_audience:
                # Это service token (от другого микросервиса)
                await self.app(scope, receive, send)
                return
            
            # Это user token — проверяем бан
            character_id_str = payload.get("character_id")
            if not character_id_str:
                await self.app(scope, receive, send)
                return

            if await self.redis.exists(f"banned_character:{character_id_str}"):
                logger.warning(f"Banned character {character_id_str} attempted to access {path}")
                await self._send_403(send)
                return

        except Exception as e:
            logger.debug(f"Ban check skipped for {path}: {e}")

        await self.app(scope, receive, send)

    async def _legacy_path(self, scope, receive, send, path):
        """Старый путь через decode_service для обратной совместимости"""
        if not self.decode_service:
            await self.app(scope, receive, send)
            return

        token = None
        headers = dict(scope.get("headers", []))

        auth_header = headers.get(b"authorization")
        if auth_header:
            auth_header_str = auth_header.decode("utf-8")
            if auth_header_str.startswith("Bearer "):
                token = auth_header_str.split(" ")[1]

        if not token:
            cookie_header = headers.get(b"cookie")
            if cookie_header:
                cookie_str = cookie_header.decode("utf-8")
                cookies = dict(item.split("=", 1) for item in cookie_str.split("; ") if "=" in item)
                token = cookies.get("access_token")

        if not token:
            await self.app(scope, receive, send)
            return

        try:
            token_data = self.decode_service.decode_access_token(token)
            character_id = getattr(token_data, 'character_id', None)

            if not character_id:
                await self.app(scope, receive, send)
                return

            if await self.redis.exists(f"banned_character:{character_id}"):
                logger.warning(f"Banned character {character_id} attempted to access {path}")
                await self._send_403(send)
                return

        except Exception as e:
            logger.debug(f"Ban check skipped for {path}: {e}")

        await self.app(scope, receive, send)

    async def _send_403(self, send):
        """Отправить 403 Forbidden ответ"""
        await send({
            'type': 'http.response.start',
            'status': status.HTTP_403_FORBIDDEN,
            'headers': [
                (b'content-type', b'application/json'),
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': json.dumps({"detail": "Character is banned"}).encode("utf-8"),
        })