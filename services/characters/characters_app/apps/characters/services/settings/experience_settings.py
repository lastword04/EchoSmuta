import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from ...repositories.settings.experience_settings import GlobalCharacterExperienceSettingsRepositoryProtocol
from ...schemas import (
    GlobalCharacterExperienceSettingsCreateSchema,
    GlobalCharacterExperienceSettingsUpdateSchema,
    GlobalCharacterExperienceSettingsUpdateDBSchema,
    GlobalCharacterExperienceSettingsReadSchema
)

class GlobalCharacterExperienceSettingsServiceProtocol(Protocol):
    repository: GlobalCharacterExperienceSettingsRepositoryProtocol

    async def get(self: Self, id: uuid.UUID) -> GlobalCharacterExperienceSettingsReadSchema:
        ...

    async def create(self: Self, data: GlobalCharacterExperienceSettingsCreateSchema) -> GlobalCharacterExperienceSettingsReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: GlobalCharacterExperienceSettingsUpdateSchema) -> GlobalCharacterExperienceSettingsReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def bulk_create(self: Self, data: list[GlobalCharacterExperienceSettingsCreateSchema]) -> list[GlobalCharacterExperienceSettingsReadSchema]:
       ...

    async def get_all(self: Self) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        ...

    async def find_by_level_and_max_experience(self: Self, level: int, experience: int) -> Optional[GlobalCharacterExperienceSettingsReadSchema]:
        ...    

    async def find_all_by_level_and_max_experience(self: Self, level: int, experience: int) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        ...        

class GlobalCharacterExperienceSettingsService(GlobalCharacterExperienceSettingsServiceProtocol):
    def __init__(self: Self, repository: GlobalCharacterExperienceSettingsRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> GlobalCharacterExperienceSettingsReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: GlobalCharacterExperienceSettingsCreateSchema) -> GlobalCharacterExperienceSettingsReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: GlobalCharacterExperienceSettingsUpdateSchema) -> GlobalCharacterExperienceSettingsReadSchema:
        experience_character_settings_update_data = GlobalCharacterExperienceSettingsUpdateDBSchema(**data.model_dump(),
                                                               id=id
        )
        return await self.repository.update(id, experience_character_settings_update_data)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def bulk_create(self: Self, data: list[GlobalCharacterExperienceSettingsCreateSchema]) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        return await self.repository.bulk_create(data)

    async def get_all(self: Self) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        return await self.repository.get_all()
    
    async def find_by_level_and_max_experience(self: Self, level: int, experience: int) -> Optional[GlobalCharacterExperienceSettingsReadSchema]:
        # Делегируем поиск в репозиторий
        return await self.repository.find_by_level_and_max_experience(level, experience)
    
    async def find_all_by_level_and_max_experience(self: Self, level: int, experience: int) -> list[GlobalCharacterExperienceSettingsReadSchema]:
        return await self.repository.find_all_by_level_and_max_experience(level, experience)