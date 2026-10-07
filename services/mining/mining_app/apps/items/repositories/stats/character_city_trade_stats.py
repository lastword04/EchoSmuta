import uuid
from typing import Protocol

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import CharacterCityTradeStats
from ...schemas import (
    CharacterCityTradeStatsCreateSchema,
    CharacterCityTradeStatsReadSchema,
)


class CharacterCityTradeStatsRepositoryProtocol(Protocol):
    async def get_or_create(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema:
        """Получить или создать статистику персонажа для локации"""
        ...

    async def update_experience_and_level(
        self, character_id: uuid.UUID, location_slug: str, level: int, experience: int
    ) -> bool:
        """Обновить опыт и уровень персонажа"""
        ...

    # Оставляем старые методы для обратной совместимости
    async def create(self, data: CharacterCityTradeStatsCreateSchema) -> CharacterCityTradeStatsReadSchema:
        ...

    async def get_by_character_and_location(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema | None:
        ...


class CharacterCityTradeStatsRepository(CharacterCityTradeStatsRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema:
        """Получить или создать статистику персонажа для локации"""
        async with self.session as session, session.begin():
            # 1. Пробуем найти существующую запись
            stmt = (
                sa.select(CharacterCityTradeStats)
                .where(
                    CharacterCityTradeStats.character_id == character_id,
                    CharacterCityTradeStats.location_slug == location_slug
                )
            )
            result = await session.execute(stmt)
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
            model = (await session.execute(stmt)).scalar_one()

            return CharacterCityTradeStatsReadSchema.model_validate(model, from_attributes=True)

    async def update_experience_and_level(
        self, character_id: uuid.UUID, location_slug: str, level: int, experience: int
    ) -> bool:
        """Обновить опыт и уровень персонажа"""
        async with self.session as session, session.begin():
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
            await session.execute(stmt)
            return True

    # Оставляем старые методы для обратной совместимости
    async def create(self, data: CharacterCityTradeStatsCreateSchema) -> CharacterCityTradeStatsReadSchema:
        stats = CharacterCityTradeStats(**data.model_dump())
        self.session.add(stats)
        await self.session.commit()
        await self.session.refresh(stats)
        return CharacterCityTradeStatsReadSchema.model_validate(stats)

    async def get_by_character_and_location(
        self, character_id: uuid.UUID, location_slug: str
    ) -> CharacterCityTradeStatsReadSchema | None:
        stmt = select(CharacterCityTradeStats).where(
            CharacterCityTradeStats.character_id == character_id,
            CharacterCityTradeStats.location_slug == location_slug
        )
        result = await self.session.execute(stmt)
        stats = result.scalar_one_or_none()
        return CharacterCityTradeStatsReadSchema.model_validate(stats) if stats else None