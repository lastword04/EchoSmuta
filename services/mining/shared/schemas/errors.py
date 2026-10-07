from pydantic import BaseModel
from typing import Any, Optional


class BaseResponseSchema(BaseModel):
    """
    Базовая схема для стандартных ответов об ошибках между микросервисами.
    Используется для единообразного формата ошибок во всем приложении.
    """
    detail: str
    """Человекочитаемое описание ошибки"""
    
    error_code: str
    """Уникальный код ошибки для программной обработки"""
    
    error_type: Optional[str] = None
    """Тип ошибки (соответствует имени класса исключения)"""

    extras: Optional[dict[str, Any]] = None
    """Дополнительные данные, специфичные для конкретной ошибки"""