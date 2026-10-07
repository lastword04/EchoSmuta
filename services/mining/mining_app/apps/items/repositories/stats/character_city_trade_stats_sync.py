import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ...models import CharacterCityTradeStats
from ...schemas import (
    CharacterCityTradeStatsCreateSchema,
    CharacterCityTradeStatsReadSchema,
)


class CharacterCityTradeStatsSyncRepository:
    """Синхронная версия репозитория для CharacterCityTradeStats (для Celery)"""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create(
        self,
        character_id: uuid.UUID,
        location_slug: str
    ) -> CharacterCityTradeStatsReadSchema:
        """Получить или создать статистику персонажа для локации"""
        # 1. Пробуем найти существующую запись
        stmt = (
            sa.select(CharacterCityTradeStats)
            .where(
                CharacterCityTradeStats.character_id == character_id,
                CharacterCityTradeStats.location_slug == location_slug
            )
        )
        result = self.session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance:
            return CharacterCityTradeStatsReadSchema.model_validate(instance, from_attributes=True)

        # 2. Создаём новую запись
        create_data = CharacterCityTradeStatsCreateSchema(
            character_id=character_id,
            location_slug=location_slug
        )

        stmt = (
            sa.insert(CharacterCityTradeStats)
            .values(**create_data.model_dump(exclude={'id'}))
            .returning(CharacterCityTradeStats)
        )
        model = self.session.execute(stmt).scalar_one()

        return CharacterCityTradeStatsReadSchema.model_validate(model, from_attributes=True)

    def update_experience_and_level(
        self,
        character_id: uuid.UUID,
        location_slug: str,
        level: int,
        experience: int
    ) -> bool:
        """Обновить опыт и уровень персонажа"""
        stmt = (
            sa.update(CharacterCityTradeStats)
            .where(
                CharacterCityTradeStats.character_id == character_id,
                CharacterCityTradeStats.location_slug == location_slug
            )
            .values(
                level=level,
                experience=experience
            )
        )
        self.session.execute(stmt)
        return True

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()