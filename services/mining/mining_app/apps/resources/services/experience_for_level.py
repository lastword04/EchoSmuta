from typing import Protocol

from ..repositories.experience_for_level import ExperienceForLevelRepositoryProtocol
from ..schemas import ExperienceForLevelCreateSchema, ExperienceForLevelReadSchema


class ExperienceForLevelServiceProtocol(Protocol):
    async def get_experience_for_next_level(
        self,
        current_level: int
    ) -> ExperienceForLevelReadSchema | None:
        """
        Получает опыт, необходимый для следующего уровня после current_level.
        Если следующего уровня нет, возвращает None.
        """
        ...

    async def bulk_create_experience_levels(
        self,
        experience_levels: list[ExperienceForLevelCreateSchema]
    ) -> list[ExperienceForLevelReadSchema]:
        """
        Создает несколько записей опыта для уровней за один вызов.
        """
        ...

    async def get_all_experiences_for_level(self) -> list[ExperienceForLevelReadSchema]:
        """
        Получает все записи опыта для уровней.
        """
        ...

    async def get_current_and_next_level_experience(
        self,
        current_level: int
    ) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]:
        """
        Получает опыт для текущего и следующего уровней.
        Возвращает кортеж: (текущий уровень или None, следующий уровень или None).
        """
        ...

    async def get_current_level(
            self,
            current_level: int
    ) -> ExperienceForLevelReadSchema:
        ...

class ExperienceForLevelService(ExperienceForLevelServiceProtocol):
    def __init__(self, repository: ExperienceForLevelRepositoryProtocol):
        self.repository = repository

    async def get_experience_for_next_level(
        self,
        current_level: int
    ) -> ExperienceForLevelReadSchema | None:
        return await self.repository.get_next_level_experience(current_level)

    async def bulk_create_experience_levels(
        self,
        experience_levels: list[ExperienceForLevelCreateSchema]
    ) -> list[ExperienceForLevelReadSchema]:
        return await self.repository.bulk_create(experience_levels)

    async def get_all_experiences_for_level(self) -> list[ExperienceForLevelReadSchema]:
        return await self.repository.get_all()
    
    async def get_current_and_next_level_experience(
        self,
        current_level: int
    ) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]:
        return await self.repository.get_current_and_next_level_experience(current_level)
    
    async def get_current_level(
            self,
            current_level: int
    ) -> ExperienceForLevelReadSchema:
        return await self.repository.get_current_level(current_level)