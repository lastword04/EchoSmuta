from celery import Celery
import time
import asyncio
from ...core.db import AsyncSessionFactory
from ...core.celery import get_celery_app
from ...settings import settings
from ..rest.depends import (
    get_expire_rentals_use_case_factory,
    get_expire_house_requests_use_case_factory,
    get_house_guest_service_factory,
    get_wear_house_furniture_use_case_factory,
)
from .deps import (
    get_cleanup_detached_characters_use_case,
    get_change_inactive_use_case_factory,
    get_cleanup_acitvity_use_case
)
from ..stats.depends import get_passive_regeneration_use_case_factory

import logging

logger = logging.getLogger(__name__)
celery_app: Celery = get_celery_app()


@celery_app.task
def cleanup_detached_characters() -> bool:
    try:
        result = asyncio.run(_cleanup_detached_characters_async())
        logger.info(f"Cleanup detached characters completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cleanup detached characters failed: {e}")
        raise


async def _cleanup_detached_characters_async() -> bool:
    async with AsyncSessionFactory() as session:
        use_case = get_cleanup_detached_characters_use_case(session=session)
        return await use_case()


@celery_app.task
def cleanup_old_character_activity() -> bool:
    try:
        result = asyncio.run(_cleanup_old_activity_async())
        logger.info(f"Cleanup old characters activities completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cleanup old characters activities failed: {e}")
        raise


async def _cleanup_old_activity_async() -> bool:
    async with AsyncSessionFactory() as session:
        use_case = get_cleanup_acitvity_use_case(session=session, settings=settings)
        return await use_case()


@celery_app.task
def change_status_characters() -> bool:
    try:
        result = asyncio.run(_change_status_for_inactive_characters_async())
        logger.info(f"Change status for inactive characters: {result}")
        return result
    except Exception as e:
        logger.error(f"Change status for inactive characters failed: {e}")
        raise


async def _change_status_for_inactive_characters_async() -> bool:
    """Деактивация неактивных персонажей"""
    import redis.asyncio as aioredis
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    engine = create_async_engine(settings.db.dsn)
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            house_guest_service = get_house_guest_service_factory(
                session=session,
                settings=settings,
                redis_client=redis_client,
            )
            use_case = get_change_inactive_use_case_factory(
                session=session,
                settings=settings,
                redis_client=redis_client,
                house_guest_service=house_guest_service,
            )
            return await use_case()
    finally:
        await redis_client.aclose()
        await engine.dispose()


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    retry_backoff=2,
    retry_jitter=True
)
def passive_regeneration(self) -> int:
    """Периодическая задача для базовой регенерации всех активных персонажей"""
    try:
        result = asyncio.run(_passive_regeneration_async())
        logger.info(f"Passive regeneration completed: processed {result} characters")
        return result
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"Passive regeneration connection error (will retry): {e}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Passive regeneration failed: {e}")
        raise


async def _passive_regeneration_async() -> int:
    """
    Пассивная регенерация.
    Engine и Redis создаются на каждый запуск: Celery крутит каждую задачу
    в новом event loop, а модульные соединения (AsyncSessionFactory,
    get_redis_client) остаются привязаны к старому loop.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import redis.asyncio as aioredis

    start_time = time.time()
    engine = create_async_engine(settings.db.dsn)
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            use_case = get_passive_regeneration_use_case_factory(
                session=session,
                redis_client=redis_client,
            )
            result = await use_case()
        elapsed = time.time() - start_time
        logger.info(f"Passive regeneration: {result} chars in {elapsed:.3f}s")
        return result
    finally:
        await redis_client.aclose()
        await engine.dispose()


@celery_app.task
def expire_rest_rentals() -> int:
    """Периодическая задача для обработки истёкших аренд"""
    try:
        result = asyncio.run(_expire_rest_rentals_async())
        logger.info(f"Expire rest rentals completed: {result} rentals expired")
        return result
    except Exception as e:
        logger.error(f"Expire rest rentals failed: {e}")
        raise


async def _expire_rest_rentals_async() -> int:
    """Обработка истёкших аренд."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import redis.asyncio as aioredis

    engine = create_async_engine(settings.db.dsn)
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            use_case = get_expire_rentals_use_case_factory(
                session=session,
                redis_client=redis_client,
            )
            result = await use_case()
        return result
    finally:
        await redis_client.aclose()
        await engine.dispose()


@celery_app.task
def expire_house_requests() -> int:
    """Периодическая задача для обработки истёкших заявок на вход в дом"""
    try:
        result = asyncio.run(_expire_house_requests_async())
        logger.info(f"Expire house requests completed: {result} requests expired")
        return result
    except Exception as e:
        logger.error(f"Expire house requests failed: {e}")
        raise


async def _expire_house_requests_async() -> int:
    """Обработка истёкших заявок на вход в дом."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import redis.asyncio as aioredis

    engine = create_async_engine(settings.db.dsn)
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            use_case = get_expire_house_requests_use_case_factory(
                session=session,
                redis_client=redis_client,
            )
            result = await use_case()
        return result
    finally:
        await redis_client.aclose()
        await engine.dispose()


@celery_app.task
def wear_house_furniture() -> int:
    """Периодическая задача износа мебели в домах"""
    try:
        result = asyncio.run(_wear_house_furniture_async())
        logger.info(f"Wear house furniture completed: {result} items processed")
        return result
    except Exception as e:
        logger.error(f"Wear house furniture failed: {e}")
        raise


async def _wear_house_furniture_async() -> int:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import redis.asyncio as aioredis

    engine = create_async_engine(settings.db.dsn)
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            use_case = get_wear_house_furniture_use_case_factory(
                session=session,
                redis_client=redis_client,
            )
            return await use_case()
    finally:
        await redis_client.aclose()
        await engine.dispose()