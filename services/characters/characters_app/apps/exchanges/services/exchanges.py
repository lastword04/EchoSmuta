import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.exchanges import ExchangeSettingsRepositoryProtocol
from ..schemas import (
    ExchangeSettingsCreateSchema,
    ExchangeSettingsReadSchema,
    ExchangeSettingsUpdateDBSchema,
    ExchangeSettingsUpdateSchema
)

class ExchangeSettingsServiceProtocol(Protocol):
    repository: ExchangeSettingsRepositoryProtocol

    async def create(self: Self, data: ExchangeSettingsCreateSchema) -> ExchangeSettingsReadSchema:
        ...

    async def get(self: Self, id: uuid.UUID) -> ExchangeSettingsReadSchema:
        ...
    
    async def update(self: Self, id: uuid.UUID, data: ExchangeSettingsUpdateSchema) -> ExchangeSettingsReadSchema:
        ...
    
    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def get_all(self: Self) -> list[ExchangeSettingsReadSchema]:
        ...

class ExchangeSettingsService(ExchangeSettingsServiceProtocol):
    def __init__(self, repository: ExchangeSettingsRepositoryProtocol) -> None:
        self.repository = repository

    async def create(self, data: ExchangeSettingsCreateSchema) -> ExchangeSettingsReadSchema:
        return await self.repository.create(data)

    async def get(self, id: uuid.UUID) -> ExchangeSettingsReadSchema:
        return await self.repository.get(id)

    async def update(self, id: uuid.UUID, data: ExchangeSettingsUpdateSchema) -> ExchangeSettingsReadSchema:
        db_update = ExchangeSettingsUpdateDBSchema(
            id=id,
            **data.model_dump()
        )
        return await self.repository.update(db_update)

    async def delete(self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def get_all(self) -> list[ExchangeSettingsReadSchema]:
        return await self.repository.get_all()