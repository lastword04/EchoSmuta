import uuid
from typing import Protocol
from typing_extensions import Self
from shared.enums import Race
from ...repositories.settings.race_settings import RaceSettingsRepositoryProtocol
from ...schemas import (
    RaceSettingsReadSchema,
    RaceSettingsCreateSchema,
    RaceSettingsUpdateSchema,
    RaceSettingsUpdateDBSchema
)

class RaceSettingsServiceProtocol(Protocol):
    repository: RaceSettingsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> RaceSettingsReadSchema:
        ...

    async def create(self: Self, data: RaceSettingsCreateSchema) -> RaceSettingsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: RaceSettingsUpdateSchema) -> RaceSettingsReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def bulk_create(self: Self, data: list[RaceSettingsCreateSchema]) -> list[RaceSettingsReadSchema]:
       ...

    async def get_all(self: Self) -> list[RaceSettingsReadSchema]:
        ...

    async def get_by_race(self: Self, race: Race) -> RaceSettingsReadSchema:
        ...

class RaceSettingsService(RaceSettingsServiceProtocol):
    def __init__(self: Self, repository: RaceSettingsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> RaceSettingsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: RaceSettingsCreateSchema) -> RaceSettingsReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: RaceSettingsUpdateSchema) -> RaceSettingsReadSchema:
        race_settings_update_data = RaceSettingsUpdateDBSchema(**data.model_dump(),
                                                               id=id
        )
        return await self.repository.update(id, race_settings_update_data)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def bulk_create(self: Self, data: list[RaceSettingsCreateSchema]) -> list[RaceSettingsReadSchema]:
        return await self.repository.bulk_create(data)

    async def get_all(self: Self) -> list[RaceSettingsReadSchema]:
        return await self.repository.get_all()

    async def get_by_race(self, race: Race) -> RaceSettingsReadSchema:
        result = await self.repository.get_by_race(race)
        if not result:
            raise ValueError("Race settings not found")
        return result