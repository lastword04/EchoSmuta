from typing import Protocol

from ...repositories.items.experience_for_level import (
    ItemExperienceForLevelRepositoryProtocol,
)
from ...schemas import (
    ItemExperienceForLevelCreateSchema,
    ItemExperienceForLevelReadSchema,
)


class ItemExperienceForLevelServiceProtocol(Protocol):
    async def bulk_create(self, data: list[ItemExperienceForLevelCreateSchema]) -> list[ItemExperienceForLevelReadSchema]:
        ...

    async def get_all(self) -> list[ItemExperienceForLevelReadSchema]:
        ...

    async def get_current_level(self, current_level: int) -> ItemExperienceForLevelReadSchema:
        ...

    async def get_current_and_next_level_experience(
        self, current_level: int
    ) -> tuple[ItemExperienceForLevelReadSchema | None, ItemExperienceForLevelReadSchema | None]:
        ...

    async def get_next_level_experience(self, current_level: int) -> ItemExperienceForLevelReadSchema | None:
        ...


class ItemExperienceForLevelService(ItemExperienceForLevelServiceProtocol):
    def __init__(self, repository: ItemExperienceForLevelRepositoryProtocol):
        self.repository = repository

    async def bulk_create(self, data: list[ItemExperienceForLevelCreateSchema]) -> list[ItemExperienceForLevelReadSchema]:
        return await self.repository.bulk_create(data)

    async def get_all(self) -> list[ItemExperienceForLevelReadSchema]:
        return await self.repository.get_all()

    async def get_current_level(self, current_level: int) -> ItemExperienceForLevelReadSchema:
        return await self.repository.get_current_level(current_level)

    async def get_current_and_next_level_experience(
        self, current_level: int
    ) -> tuple[ItemExperienceForLevelReadSchema | None, ItemExperienceForLevelReadSchema | None]:
        return await self.repository.get_current_and_next_level_experience(current_level)

    async def get_next_level_experience(self, current_level: int) -> ItemExperienceForLevelReadSchema | None:
        return await self.repository.get_next_level_experience(current_level)