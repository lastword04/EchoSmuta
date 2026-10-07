from jose import jwt, JWTError
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging
from ...settings import settings
from ...core.utils.exceptions import PermissionDeniedError

logger = logging.getLogger(__name__)

def create_service_token(
    target_service: str,
    permissions: List[str],
    expire_minutes: Optional[int] = None
) -> str:
    """
    Создает JWT для межмикросервисного взаимодействия
    
    :param target_service: Целевой сервис (поле aud)
    :param permissions: Список разрешений
    :param expire_hours: Срок жизни в часах (по умолчанию из настроек)
    """
    # Используем timezone-aware объекты для корректной работы с UTC
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.service_name,
        "aud": target_service,
        "permissions": permissions,
        "exp": now + timedelta(minutes=expire_minutes or settings.service_jwt.expire_minutes),
        "iat": now,
        "jti": str(int(time.time() * 1000))  # Уникальный ID для отслеживания
    }
    return jwt.encode(
        payload,
        settings.service_jwt.secret_key,
        algorithm=settings.service_jwt.algorithm
    )

def decode_service_token(token: str, expected_audience: str) -> Dict:
    """
    Декодирует и проверяет сервисный JWT
    
    :param token: Токен для проверки
    :param expected_audience: Ожидаемый получатель (должен совпадать с aud в токене)
    """
    try:
        payload = jwt.decode(
            token,
            settings.service_jwt.secret_key,
            algorithm=settings.service_jwt.algorithm,
            audience=expected_audience
        )
        return payload
    except JWTError:
        logger.error("Invalid service token: %s", token)
        raise PermissionDeniedError()