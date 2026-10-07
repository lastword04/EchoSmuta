import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import CharacterLocationStats
from ..schemas import CharacterLocationStatsCreateSchema, CharacterLocationStatsReadSchema


class CharacterLocationStatsSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create(
        self,
        character_id: uuid.UUID,
        location_slug: str
    ) -> CharacterLocationStatsReadSchema:
        # 1. Пробуем найти существующую запись
        stmt = (
            sa.select(CharacterLocationStats)
            .where(
                CharacterLocationStats.character_id == character_id,
                CharacterLocationStats.location_slug == location_slug
            )
        )
        result = self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance:
            return CharacterLocationStatsReadSchema.model_validate(instance, from_attributes=True)

        # 2. Создаём новую запись
        create_data = CharacterLocationStatsCreateSchema(
            character_id=character_id,
            location_slug=location_slug
        )

        stmt = (
            sa.insert(CharacterLocationStats)
            .values(**create_data.model_dump(exclude={'id'}))
            .returning(CharacterLocationStats)
        )
        model = self.session.execute(stmt).scalar_one()

        return CharacterLocationStatsReadSchema.model_validate(model, from_attributes=True)

    def update_experience_and_level_and_add_chance(
        self,
        character_id: uuid.UUID,
        location_slug: str,
        level: int,
        experience: int,
        add_chance: float
    ) -> bool:
        stmt = (
            sa.update(CharacterLocationStats)
            .where(
                CharacterLocationStats.character_id == character_id,
                CharacterLocationStats.location_slug == location_slug
            )
            .values(
                level=level,
                experience=experience,
                add_chance=add_chance
            )
        )
        self.session.execute(stmt)
        return True

    def update_add_chance(
        self,
        character_id: uuid.UUID,
        location_slug: str,
        add_chance: float
    ) -> bool:
        stmt = (
            sa.update(CharacterLocationStats)
            .where(
                CharacterLocationStats.character_id == character_id,
                CharacterLocationStats.location_slug == location_slug
            )
            .values(add_chance=add_chance)
        )
        self.session.execute(stmt)
        return True

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()