import uuid
from typing import Protocol
from typing_extensions import Self
from ...repositories.settings.global_settings import GlobalCharacterSettingsRepositoryProtocol
from ...schemas import (
    GlobalCharacterSettingsCreateSchema,
    GlobalCharacterSettingsUpdateSchema,
    GlobalCharacterSettingsUpdateDBSchema,
    GlobalCharacterSettingsReadSchema
)

class GlobalCharacterSettingsServiceProtocol(Protocol):
    repository: GlobalCharacterSettingsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> GlobalCharacterSettingsReadSchema:
        ...

    async def create(self: Self, data: GlobalCharacterSettingsCreateSchema) -> GlobalCharacterSettingsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: GlobalCharacterSettingsUpdateSchema) -> GlobalCharacterSettingsReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def bulk_create(self: Self, data: list[GlobalCharacterSettingsCreateSchema]) -> list[GlobalCharacterSettingsReadSchema]:
       ...

    async def get_all(self: Self) -> list[GlobalCharacterSettingsReadSchema]:
        ...

class GlobalCharacterSettingsService(GlobalCharacterSettingsServiceProtocol):
    def __init__(self: Self, repository: GlobalCharacterSettingsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> GlobalCharacterSettingsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: GlobalCharacterSettingsCreateSchema) -> GlobalCharacterSettingsReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: GlobalCharacterSettingsUpdateSchema) -> GlobalCharacterSettingsReadSchema:
        global_character_settings_update_data = GlobalCharacterSettingsUpdateDBSchema(**data.model_dump(),
                                                               id=id
        )
        return await self.repository.update(id, global_character_settings_update_data)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def bulk_create(self: Self, data: list[GlobalCharacterSettingsCreateSchema]) -> list[GlobalCharacterSettingsReadSchema]:
        return await self.repository.bulk_create(data)

    async def get_all(self: Self) -> list[GlobalCharacterSettingsReadSchema]:
        return await self.repository.get_all()