import redis.asyncio as redis
from typing import Optional, Dict, List
from abc import ABC
import json
from typing import TypeVar, Generic
from typing_extensions import Self

T = TypeVar('T')  # Тип данных для сериализации

class BaseRedisRepository(ABC, Generic[T]):
    """Базовый репозиторий для Redis с переиспользуемыми методами"""
    
    def __init__(self: Self, redis_client: redis.Redis, prefix: str = ""):
        self.redis_client = redis_client
        self.prefix = prefix
    
    def _make_key(self: Self, key: str) -> str:
        """Создает ключ с префиксом"""
        return f"{self.prefix}:{key}" if self.prefix else key
    
    async def set(self: Self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Устанавливает значение по ключу"""
        redis_key = self._make_key(key)
        serialized_value = self._serialize(value)
        
        if ttl:
            await self.redis_client.setex(redis_key, ttl, serialized_value)
        else:
            await self.redis_client.set(redis_key, serialized_value)
    
    async def get(self: Self, key: str) -> Optional[T]:
        """Получает значение по ключу"""
        redis_key = self._make_key(key)
        result = await self.redis_client.get(redis_key)
        
        if result is None:
            return None
            
        return self._deserialize(result)
    
    async def delete(self: Self, key: str) -> bool:
        """Удаляет значение по ключу"""
        redis_key = self._make_key(key)
        result = await self.redis_client.delete(redis_key)
        return bool(result)
    
    async def exists(self: Self, key: str) -> bool:
        """Проверяет существование ключа"""
        redis_key = self._make_key(key)
        return bool(await self.redis_client.exists(redis_key))

    async def expire(self: Self, key: str, ttl: int) -> bool:
        """Устанавливает TTL для ключа"""
        redis_key = self._make_key(key)
        return bool(await self.redis_client.expire(redis_key, ttl))

    async def get_ttl(self: Self, key: str) -> int:
        """Получает оставшееся время жизни ключа"""
        redis_key = self._make_key(key)
        return await self.redis_client.ttl(redis_key)

    async def set_many(self: Self, data: Dict[str, T], ttl: Optional[int] = None) -> None:
        """Устанавливает несколько значений"""
        pipe = self.redis_client.pipeline()
        
        for key, value in data.items():
            redis_key = self._make_key(key)
            serialized_value = self._serialize(value)
            
            if ttl:
                pipe.setex(redis_key, ttl, serialized_value)
            else:
                pipe.set(redis_key, serialized_value)
        
        await pipe.execute()

    async def get_many(self: Self, keys: List[str]) -> Dict[str, Optional[T]]:
        """Получает несколько значений"""
        redis_keys = [self._make_key(key) for key in keys]
        results = await self.redis_client.mget(redis_keys)
        
        return {
            key: self._deserialize(result) if result else None
            for key, result in zip(keys, results)
        }
    
    def _serialize(self: Self, value: T) -> str:
        """Сериализует значение в строку"""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        else:
            # Для Pydantic моделей и других объектов
            if hasattr(value, 'model_dump'):
                return json.dumps(value.model_dump(), ensure_ascii=False)
            elif hasattr(value, 'dict'):
                return json.dumps(value.dict(), ensure_ascii=False)
            else:
                return json.dumps(value, ensure_ascii=False, default=str)

    def _deserialize(self, value) -> str:
        """Десериализует значение как строку"""
        if isinstance(value, bytes):
            return value.decode('utf-8')
        elif isinstance(value, str):
            return value
        else:
            raise TypeError(f"Expected bytes or str, got {type(value)}")