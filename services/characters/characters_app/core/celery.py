# celery.py
import logging
from typing import Optional
from celery import Celery
from ..settings import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр Celery приложения
_celery_app: Optional[Celery] = None

def get_celery_app() -> Celery:
    global _celery_app
    
    if _celery_app is not None:
        return _celery_app
    
    try:
        _celery_app = Celery(
            "characters-app",
            broker=settings.celery.broker_url,
            backend=settings.celery.result_backend,
        )
        
        # Базовая конфигурация Celery
        _celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone=settings.celery.timezone,
            enable_utc=True,
            broker_connection_retry_on_startup=True,
            beat_scheduler="redbeat.RedBeatScheduler",
            redbeat_redis_url=settings.celery.redbeat_redis_url,
            redbeat_key_prefix="redbeat:characters:",
        )
        
        logger.info(f"Celery app created with broker: {settings.celery.broker_url}")
        return _celery_app
        
    except Exception as e:
        logger.error(f"Failed to create Celery app: {e}")
        raise

# Создаем экземпляр приложения
app = get_celery_app()

def close_celery_app() -> None:
    """Закрывает Celery приложение"""
    global _celery_app
    if _celery_app is not None:
        _celery_app = None
        logger.info("Celery app reference cleared")