import asyncio
import logging
import time
from typing import Dict, List

from jose import jwt

from .jwt import create_service_token

logger = logging.getLogger(__name__)

# Упреждающее обновление: если до exp кешированного токена осталось меньше
# этого буфера, get_token выдаёт новый токен. Это гарантирует, что токен
# не протухнет между получением и использованием даже при долгих вызовах.
EXPIRY_REFRESH_BUFFER_SECONDS = 5 * 60


class ServiceTokenManager:
    """Менеджер сервисных токенов для межсервисного взаимодействия.

    Кеш хранит токен вместе с его exp и никогда не отдаёт «мёртвый» токен.
    Токен перевыпускается, если:
      - его нет в кеше;
      - или до его exp осталось меньше EXPIRY_REFRESH_BUFFER_SECONDS (5 минут) —
        упреждающее обновление;
      - или передан force=True — реактивное обновление после ответа
        401 token expired от целевого сервиса.

    Фоновый refresh-цикл не нужен: корректность обеспечивает сам get_token,
    который при каждом вызове проверяет exp кешированного токена. Поэтому
    «вечное» хранение токена и initialize() со стартом фонового цикла убраны:
    initialize() оставлен как no-op для обратной совместимости.
    """

    def __init__(self):
        self.tokens: Dict[str, dict] = {}  # cache_key -> {"token": str, "exp": float}
        self.lock = asyncio.Lock()

    @staticmethod
    def _cache_key(target_service: str, permissions: List[str]) -> str:
        return f"{target_service}:{','.join(sorted(permissions))}"

    @staticmethod
    def _token_expiry(token: str) -> float:
        """Достаёт exp из токена без проверки подписи (подпись своя)."""
        try:
            claims = jwt.get_unverified_claims(token)
            return float(claims.get("exp") or 0.0)
        except Exception:  # noqa: BLE001 — нечитаемый токен = форсировать перевыпуск
            logger.warning("Failed to read exp from service token, will reissue")
            return 0.0

    async def get_token(
        self, target_service: str, permissions: List[str], force: bool = False
    ) -> str:
        """Возвращает валидный токен для целевого сервиса.

        :param force: True — игнорировать кеш и выпустить новый токен
            (например, после ответа 401 token expired от целевого сервиса).
        """
        cache_key = self._cache_key(target_service, permissions)
        async with self.lock:
            cached = self.tokens.get(cache_key)
            if (
                not force
                and cached is not None
                and (cached["exp"] - time.time()) > EXPIRY_REFRESH_BUFFER_SECONDS
            ):
                return cached["token"]

            token = create_service_token(
                target_service=target_service,
                permissions=permissions,
            )
            expiry = self._token_expiry(token)
            self.tokens[cache_key] = {"token": token, "exp": expiry}
            logger.debug(
                "Service token for %s reissued (force=%s, ttl=%.0fs)",
                target_service,
                force,
                expiry - time.time(),
            )
            return token

    async def invalidate(self, target_service: str, permissions: List[str]) -> None:
        """Сбрасывает кешированный токен (например, после 401 от целевого сервиса)."""
        async with self.lock:
            self.tokens.pop(self._cache_key(target_service, permissions), None)

    async def initialize(self) -> None:
        """Совместимость со старым API: вызов на старте больше не обязателен —
        упреждающее обновление выполняется самим get_token()."""
        return None