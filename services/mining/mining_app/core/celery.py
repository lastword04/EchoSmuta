import logging
import sys
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

# Добавляем корень проекта (папку services) в PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # services/
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ..settings import settings

logger = logging.getLogger(__name__)

_celery_app: Celery | None = None

def get_celery_app() -> Celery:
    global _celery_app
    if _celery_app is not None:
        return _celery_app

    try:
        _celery_app = Celery(
            "mining-app",
            broker=settings.celery.broker_url,
            backend=settings.celery.result_backend,
        )

        _celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone=settings.celery.timezone,
            enable_utc=True,
            broker_connection_retry_on_startup=True,
            task_default_queue='mining',
            beat_scheduler="redbeat.RedBeatScheduler",
            redbeat_redis_url=settings.celery.redbeat_redis_url,
            redbeat_key_prefix="redbeat:mining:",

            beat_schedule={
                "expire-deals-every-minute": {"task": "mining.expire_deals", "schedule": 60.0, "options": {"queue": "mining"},},
                "recover-completing-deals-every-minute": {"task": "mining.recover_completing_deals", "schedule": 60.0, "options": {"queue": "mining"},},
                "cleanup-expired-items-every-5-min": {"task": "mining.cleanup_expired_items", "schedule": 300.0, "options": {"queue": "mining"},},
                "cleanup-sale-history-daily": {
                    "task": "mining.cleanup_sale_history",
                    "schedule": crontab(hour=3, minute=0),  # каждый день в 3:00 UTC
                    "args": (180,),  # хранить 180 дней = полгода
                    "options": {"queue": "mining"},
                },
            },
        )

        # Автоматическое обнаружение задач
        _celery_app.autodiscover_tasks([
            'mining_app.apps.resources',
            'mining_app.apps.items',
        ])

        logger.info(f"Celery app created with broker: {settings.celery.broker_url}")
        return _celery_app

    except Exception as e:
        logger.error(f"Failed to create Celery app: {e}")
        raise

# Создаём экземпляр приложения
app = get_celery_app()

def close_celery_app() -> None:
    global _celery_app
    if _celery_app is not None:
        _celery_app = None
        logger.info("Celery app reference cleared")