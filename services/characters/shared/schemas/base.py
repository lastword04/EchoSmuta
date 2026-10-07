"""
Модуль, содержащий базовые схемы.
"""

import uuid
from fastapi import Request
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from ..exceptions import InvalidTokenError


class CreateBaseModel(BaseModel):
    """
    Контракт для создания моделей.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None


class UpdateBaseModel(BaseModel):
    """
    Контракт обновления моделей.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class StatusOkSchema(BaseModel):
    """
    Схема успешного результата.
    """

    status: str = 'ok'


class PaginationSchema(BaseModel):
    """
    Схема пагинации с помощью limit и offset.
    """

    limit: int
    offset: int


T = TypeVar('T')


class PaginationResultSchema(BaseModel, Generic[T]):
    """
    Схема результата пагинации.
    """

    objects: list[T]
    count: int
    

class TimestampMixin(BaseModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),  # Используем timezone-aware datetime
        description="Дата и время создания"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),  # Используем timezone-aware datetime
        description="Дата и время последнего обновления"
    )

    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)


class CookieTokenSchema:
    def __init__(self, cookie_name: str, auto_error: bool = True):
        self.cookie_name = cookie_name
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        token = request.cookies.get(self.cookie_name)
        if not token and self.auto_error:
            raise InvalidTokenError()
        return token
    
