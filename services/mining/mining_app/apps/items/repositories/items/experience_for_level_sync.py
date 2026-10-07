import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import ItemExperienceForLevel
from ...schemas import ItemExperienceForLevelReadSchema


class ItemExperienceForLevelSyncRepository:
    """Синхронная версия репозитория для ItemExperienceForLevel (для Celery)"""

    def __init__(self, session: Session):
            self.session = session
    
    def get_current_level(self, current_level: int) -> ItemExperienceForLevelReadSchema:
        stmt = (
            sa.select(ItemExperienceForLevel)
            .where(ItemExperienceForLevel.level == current_level)
        )
        result = self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if not instance:
            raise ModelFieldNotFoundException(ItemExperienceForLevel, "level", current_level)

        return ItemExperienceForLevelReadSchema.model_validate(instance, from_attributes=True)

    def get_current_and_next_level_experience(
            self, current_level: int
        ) -> tuple[ItemExperienceForLevelReadSchema | None, ItemExperienceForLevelReadSchema | None]:
            stmt = (
                sa.select(ItemExperienceForLevel)
                .where(
                    sa.or_(
                        ItemExperienceForLevel.level == current_level,
                        ItemExperienceForLevel.level == current_level + 1
                    )
                )
            )
            result = self.session.execute(stmt)
            instances = result.scalars().all()
    
            current_instance = next((inst for inst in instances if inst.level == current_level), None)
            next_instance = next((inst for inst in instances if inst.level == current_level + 1), None)
    
            current_schema = (
                ItemExperienceForLevelReadSchema.model_validate(current_instance, from_attributes=True)
                if current_instance else None
            )
            next_schema = (
                ItemExperienceForLevelReadSchema.model_validate(next_instance, from_attributes=True)
                if next_instance else None
            )
    
            return current_schema, next_schema

    def get_next_level_experience(self, current_level: int) -> ItemExperienceForLevelReadSchema | None:
            stmt = (
                sa.select(ItemExperienceForLevel)
                .where(ItemExperienceForLevel.level == current_level + 1)
            )
            result = self.session.execute(stmt)
            instance = result.scalar_one_or_none()
    
            if not instance:
                return None
    
            return ItemExperienceForLevelReadSchema.model_validate(instance, from_attributes=True)
    
    def commit(self):
            self.session.commit()
    
    def rollback(self):
            self.session.rollback()

   