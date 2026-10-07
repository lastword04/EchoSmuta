from typing import Protocol

from ..models import ExperienceForLevel
from ..repositories.experience_for_level_sync import ExperienceForLevelSyncRepository
from ..schemas import ExperienceForLevelCreateSchema, ExperienceForLevelReadSchema


class ExperienceForLevelSyncServiceProtocol(Protocol):
    def get_experience_for_next_level(self, current_level: int) -> ExperienceForLevelReadSchema | None: ...
    def get_all_experiences_for_level(self) -> list[ExperienceForLevelReadSchema]: ...
    def get_current_and_next_level_experience(self, current_level: int) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]: ...
    def get_current_level(self, current_level: int) -> ExperienceForLevelReadSchema: ...


class ExperienceForLevelSyncService(ExperienceForLevelSyncServiceProtocol):
    def __init__(self, repository: ExperienceForLevelSyncRepository):
        self.repository = repository

    def get_experience_for_next_level(self, current_level: int) -> ExperienceForLevelReadSchema | None:
        return self.repository.get_next_level_experience(current_level)

    def get_all_experiences_for_level(self) -> list[ExperienceForLevelReadSchema]:
        stmt = self.repository.session.query(ExperienceForLevel).order_by(ExperienceForLevel.level).all()
        return [ExperienceForLevelReadSchema.model_validate(m, from_attributes=True) for m in stmt]

    def get_current_and_next_level_experience(
        self, current_level: int
    ) -> tuple[ExperienceForLevelReadSchema | None, ExperienceForLevelReadSchema | None]:
        return self.repository.get_current_and_next_level_experience(current_level)

    def get_current_level(self, current_level: int) -> ExperienceForLevelReadSchema:
        return self.repository.get_current_level(current_level)

    def bulk_create_experience_levels(self, experience_levels: list[ExperienceForLevelCreateSchema]) -> list[ExperienceForLevelReadSchema]:
        models = [ExperienceForLevel(**level.model_dump(exclude={'id'})) for level in experience_levels]
        self.repository.session.add_all(models)
        self.repository.session.flush()
        return [ExperienceForLevelReadSchema.model_validate(m, from_attributes=True) for m in models]