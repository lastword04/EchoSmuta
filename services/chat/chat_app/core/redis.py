import os
import redis.asyncio as redis
from typing import Dict
import logging
from ..settings import settings

logger = logging.getLogger(__name__)

# Словарь клиентов: ключ - PID процесса, значение - клиент.
# Это гарантирует, что каждый дочерний процесс (multiprocessing worker) 
# создаст свой собственный connection pool.
_redis_clients: Dict[int, redis.Redis] = {}

def get_redis_client() -> redis.Redis:
    """Возвращает Redis клиент для ТЕКУЩЕГО процесса"""
    pid = os.getpid()
    
    if pid in _redis_clients:
        return _redis_clients[pid]
    
    try:
        connection_kwargs = settings.redis.to_connection_kwargs()
        # Настраиваем пул соединений
        connection_kwargs.setdefault("max_connections", 100)
        connection_kwargs.setdefault("decode_responses", True)
        
        client = redis.Redis(**connection_kwargs)
        _redis_clients[pid] = client
        logger.info(f"Redis client created for PID {pid}: {settings.redis.host}:{settings.redis.port}/{settings.redis.db}")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client for PID {pid}: {e}")
        raise

async def close_redis_client() -> None:
    """Закрывает Redis клиент для ТЕКУЩЕГО процесса"""
    pid = os.getpid()
    if pid in _redis_clients:
        await _redis_clients[pid].close()
        del _redis_clients[pid]
        logger.info(f"Redis client closed for PID {pid}")