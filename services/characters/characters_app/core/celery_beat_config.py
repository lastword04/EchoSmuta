import logging
from celery.schedules import crontab
from .celery import app 
from ..settings import settings

logger = logging.getLogger(__name__)

def configure_beat_schedule() -> None:
    """Настраивает периодические задачи для Celery Beat"""
    
    schedule_config = {
        'cleanup-detached-characters': {
            'task': 'characters_app.apps.characters.tasks.cleanup_detached_characters',
            'schedule': crontab(
                hour=settings.celery.cleanup_detached_characters_cron_hour,
                minute=settings.celery.cleanup_detached_characters_cron_minute,
                day_of_week=settings.celery.cleanup_detached_characters_cron_day
            ),
            'options': {'queue': 'characters'},
        },
        'cleanup-old-character-activity': {
            'task': 'characters_app.apps.characters.tasks.cleanup_old_character_activity',
            'schedule': crontab(
                hour=settings.celery.cleanup_old_character_activity_cron_hour,
                minute=settings.celery.cleanup_old_character_activity_cron_minute,
                day_of_week=settings.celery.cleanup_old_character_activity_cron_day
            ),
            'options': {'queue': 'characters'},
        },
        'change-status-characters': {
            'task': 'characters_app.apps.characters.tasks.change_status_characters',
            'schedule': crontab(
                hour=settings.celery.change_status_characters_cron_hour,
                minute=settings.celery.change_status_characters_cron_minute,
            ),
            'options': {'queue': 'characters'},
        },
        'passive-regeneration': {
            'task': 'characters_app.apps.characters.tasks.passive_regeneration',
            'schedule': 10.0,
            'options': {'queue': 'characters'},
        },
        'expire-rest-rentals': {
            'task': 'characters_app.apps.characters.tasks.expire_rest_rentals',
            'schedule': 60.0,  # каждую минуту
            'options': {'queue': 'characters'},
        },
        'expire-house-requests': {
            'task': 'characters_app.apps.characters.tasks.expire_house_requests',
            'schedule': 10.0,  # каждые 10 секунд
            'options': {'queue': 'characters'},
        },
        'wear-house-furniture': {
            'task': 'characters_app.apps.characters.tasks.wear_house_furniture',
            'schedule': 60.0,  # каждую минуту, синхронно с house_wear_tick_seconds
            'options': {'queue': 'characters'},
        },
    }
    
    app.conf.beat_schedule = schedule_config

    logger.info(f"Beat schedule configured with timezone {settings.celery.timezone}")
    logger.info(f"Detached characters cleanup: {settings.celery.cleanup_detached_characters_cron_hour}:{settings.celery.cleanup_detached_characters_cron_minute:02d}")