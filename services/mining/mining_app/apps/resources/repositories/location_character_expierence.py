import uuid
from typing import Self

import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import CharacterLocationStats
from ..schemas import (
    CharacterLocationStatsCreateSchema,
    CharacterLocationStatsReadSchema,
    CharacterLocationStatsUpdateSchema,
)


class CharacterLocationStatsRepositoryProtocol(
    BaseRepositoryImpl[
        CharacterLocationStats,
        CharacterLocationStatsReadSchema,
        CharacterLocationStatsCreateSchema,
        CharacterLocationStatsUpdateSchema
    ]
):
    async def get_or_create(
        self: Self,
        character_id: uuid.UUID,  
        location_slug: str        
    ) -> CharacterLocationStatsReadSchema: 
        """
        Получает существующий CharacterLocationLevel или создает новый, если он не существует.
        Возвращает кортеж: (объект схемы, флаг был_ли_создан).
        """

    async def update_experience_and_level_and_add_chance(self, character_id: uuid.UUID, location_slug: str, level: int, experience: int, add_chance: float) -> bool:
        ...

    async def update_add_chance(self, character_id: uuid.UUID, location_slug: str, add_chance: float) -> bool:
        ...

class CharacterLocationStatsRepository(CharacterLocationStatsRepositoryProtocol):
    async def get_or_create(
        self: Self,
        character_id: uuid.UUID,
        location_slug: str
    ) -> CharacterLocationStatsReadSchema:
        async with self.session as session, session.begin():
            # 1. Попробуем найти существующую запись
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.location_slug == location_slug
                )
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance:
                # Запись найдена, возвращаем её и False
                return self.read_schema_type.model_validate(instance, from_attributes=True)

          
            create_data = CharacterLocationStatsCreateSchema(
                character_id=character_id,
                location_slug=location_slug
            )

            stmt = (
                    sa.insert(self.model_type)
                    .values(**create_data.model_dump(exclude={'id'}))
                    .returning(self.model_type)
                )
            model = (await session.execute(stmt)).scalar_one()
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def update_experience_and_level_and_add_chance(self, character_id: uuid.UUID, location_slug: str, level: int, experience: int, add_chance: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.location_slug == location_slug
                       )
                .values(level=level,
                        experience=experience,
                        add_chance=add_chance)
            )

            await session.execute(stmt)

            return True

    async def update_add_chance(self, character_id: uuid.UUID, location_slug: str, add_chance: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.location_slug == location_slug
                       )
                .values(add_chance=add_chance)
            )

            await session.execute(stmt)

            return True