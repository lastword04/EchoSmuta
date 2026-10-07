from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import ExperienceForLevelCreateSchema, ExperienceForLevelReadSchema
from ...services.experience_for_level import ExperienceForLevelServiceProtocol


class InitializeExperiencesForLevelUseCaseProtocol(UseCaseProtocol[list[ExperienceForLevelReadSchema]]):
    async def __call__(self: Self) -> list[ExperienceForLevelReadSchema]:
        ...


class InitializeExperiencesForLevelUseCase(InitializeExperiencesForLevelUseCaseProtocol):
    def __init__(self: Self, service: ExperienceForLevelServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[ExperienceForLevelReadSchema]:

        used_experiences = await self.service.get_all_experiences_for_level()
        default_experiences = self._get_default_experiences()
        if len(used_experiences) == len(default_experiences):
            return used_experiences
        if len(used_experiences) != 0:
            raise ValueError("Resources not corrected count.")

        return await self.service.bulk_create_experience_levels(default_experiences)

    def _get_default_experiences(self: Self) -> list[ExperienceForLevelCreateSchema]:
        return [
            ExperienceForLevelCreateSchema(
                level=1,
                experience=0,
                success_rate_one=0.25,
                success_rate_two=0.0,
                success_rate_three=0.0
            ),
             ExperienceForLevelCreateSchema(
                level=2,
                experience=600,
                success_rate_one=0.3,
                success_rate_two=0.0,
                success_rate_three=0.0
            ),
            ExperienceForLevelCreateSchema(
                level=3,
                experience=1900,
                success_rate_one=0.35,
                success_rate_two=0.0,
                success_rate_three=0.0
            ),
            ExperienceForLevelCreateSchema(
                level=4,
                experience=4000,
                success_rate_one=0.40,
                success_rate_two=0.05,
                success_rate_three=0.0
            ),
            ExperienceForLevelCreateSchema(
                level=5,
                experience=7000,
                success_rate_one=0.45,
                success_rate_two=0.07,
                success_rate_three=0.0
            ),
            ExperienceForLevelCreateSchema(
                level=6,
                experience=12000,
                success_rate_one=0.50,
                success_rate_two=0.09,
                success_rate_three=0.0
            ),
            ExperienceForLevelCreateSchema(
                level=7,
                experience=20000,
                success_rate_one=0.55,
                success_rate_two=0.11,
                success_rate_three=0.05
            ),
            ExperienceForLevelCreateSchema(
                level=8,
                experience=32000,
                success_rate_one=0.6,
                success_rate_two=0.13,
                success_rate_three=0.07
            ),
            ExperienceForLevelCreateSchema(
                level=9,
                experience=50000,
                success_rate_one=0.66,
                success_rate_two=0.15,
                success_rate_three=0.09
            ),
        ]
    