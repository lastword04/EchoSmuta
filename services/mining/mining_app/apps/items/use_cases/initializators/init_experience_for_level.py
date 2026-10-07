from typing import Protocol, Self

from ...schemas import (
    ItemExperienceForLevelCreateSchema,
    ItemExperienceForLevelReadSchema,
)
from ...services.items.experience_for_level import ItemExperienceForLevelServiceProtocol


class InitializeItemExperienceForLevelUseCaseProtocol(Protocol):
    async def __call__(self: Self) -> list[ItemExperienceForLevelReadSchema]:
            ...


class InitializeItemExperienceForLevelUseCase(InitializeItemExperienceForLevelUseCaseProtocol):
    def __init__(self: Self, service: ItemExperienceForLevelServiceProtocol):
            self.service = service

    async def __call__(self: Self) -> list[ItemExperienceForLevelReadSchema]:
        # Проверяем, есть ли уже записи
        used_experiences = await self.service.get_all()
        default_experiences = self._get_default_experiences()        
       
        if len(used_experiences) == len(default_experiences):
            return used_experiences    
       
        if len(used_experiences) != 0:
            raise ValueError("Item experience levels count mismatch. Please clear the table or adjust defaults.")        
        
        return await self.service.bulk_create(default_experiences)

    def _get_default_experiences(self) -> list[ItemExperienceForLevelCreateSchema]:
       
        return [
            ItemExperienceForLevelCreateSchema(level=1, experience=0, success_rate_one=0.40),
            ItemExperienceForLevelCreateSchema(level=2, experience=220, success_rate_one=0.44),
            ItemExperienceForLevelCreateSchema(level=3, experience=550, success_rate_one=0.48),
            ItemExperienceForLevelCreateSchema(level=4, experience=1150, success_rate_one=0.52),
            ItemExperienceForLevelCreateSchema(level=5, experience=2100, success_rate_one=0.56),
            ItemExperienceForLevelCreateSchema(level=6, experience=3500, success_rate_one=0.60),
            ItemExperienceForLevelCreateSchema(level=7, experience=5450, success_rate_one=0.64),
            ItemExperienceForLevelCreateSchema(level=8, experience=8050, success_rate_one=0.68),
            ItemExperienceForLevelCreateSchema(level=9, experience=11400, success_rate_one=0.72),
            ItemExperienceForLevelCreateSchema(level=10, experience=15600, success_rate_one=0.76),
        ]