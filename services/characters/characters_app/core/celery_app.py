import logging
from .celery import app
from .celery_beat_config import configure_beat_schedule
from ..apps.characters import tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


configure_beat_schedule()
logger.info("Celery app and beat schedule configured")

# Экспортируем приложение для Celery команд
celery_app = app