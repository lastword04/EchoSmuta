import logging
from celery.schedules import crontab
from .celery import app 
from ..settings import settings

logger = logging.getLogger(__name__)

def configure_beat_schedule() -> None:
    """Настраивает периодические задачи для Celery Beat"""
    
    schedule_config = {
        'cleanup-expired-reset-tokens': {
            'task': 'auth_app.apps.auth.tasks.cleanup_expired_reset_tokens',
            'schedule': crontab(
                hour=settings.celery.cleanup_reset_token_cron_hour,
                minute=settings.celery.cleanup_reset_token_cron_minute
            ),
        },
        'cleanup-expired-refresh-tokens': {
            'task': 'auth_app.apps.auth.tasks.cleanup_expired_refresh_tokens',
            'schedule': crontab(
                hour=settings.celery.cleanup_refresh_token_cron_hour,
                minute=settings.celery.cleanup_refresh_token_cron_minute
            ),
        },
    }
    
    app.conf.beat_schedule = schedule_config
    logger.info(f"Beat schedule configured with timezone {settings.celery.timezone}")
    logger.info(f"Reset tokens cleanup: {settings.celery.cleanup_reset_token_cron_hour}:{settings.celery.cleanup_reset_token_cron_minute:02d}")
    logger.info(f"Refresh tokens cleanup: {settings.celery.cleanup_refresh_token_cron_hour}:{settings.celery.cleanup_refresh_token_cron_minute:02d}")