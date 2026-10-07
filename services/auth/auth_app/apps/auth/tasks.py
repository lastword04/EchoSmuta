from celery import Celery
import asyncio
from ...core.db import AsyncSessionFactory
from ...core.celery import get_celery_app  
from ...settings import settings
from .depends import get_cleanup_reset_token_use_case, get_cleanup_refresh_token_use_case
import logging

logger = logging.getLogger(__name__)
celery_app: Celery = get_celery_app()

@celery_app.task
def cleanup_expired_reset_tokens() -> bool:
    """Периодическая задача для очистки просроченных reset токенов"""
    try:
        result = asyncio.run(_cleanup_expired_reset_tokens_async())
        logger.info(f"Cleanup expired reset tokens completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cleanup expired reset tokens failed: {e}")
        raise

async def _cleanup_expired_reset_tokens_async() -> bool:
    """Асинхронная реализация очистки токенов"""
    async with AsyncSessionFactory() as session:
        # Создаем use case
        use_case = get_cleanup_reset_token_use_case(session=session, settings=settings)
        # Выполняем очистку
        return await use_case()
    
@celery_app.task
def cleanup_expired_refresh_tokens() -> bool:
    """Периодическая задача для очистки просроченных refresh токенов"""
    try:
        result = asyncio.run(_cleanup_expired_refresh_tokens_async())
        logger.info(f"Cleanup expired refresh tokens completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cleanup expired refresh tokens failed: {e}")
        raise


async def _cleanup_expired_refresh_tokens_async() -> bool:
    async with AsyncSessionFactory() as session:
        use_case = get_cleanup_refresh_token_use_case(session=session, settings=settings)
        return await use_case()