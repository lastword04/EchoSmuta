import uuid
from typing import Self

import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import CharacterResource
from ..schemas import (
    CharacterResourceCreateSchema,
    CharacterResourceReadSchema,
    CharacterResourceUpdateSchema,
)


class CharacterResourceRepositoryProtocol(
    BaseRepositoryImpl[
        CharacterResource,
        CharacterResourceReadSchema,
        CharacterResourceCreateSchema,
        CharacterResourceUpdateSchema
    ]
):
    async def increment_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        increment: int
    ) -> bool:
        ...

    async def decrement_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        decrement: int
    ) -> bool:
        ...

    async def get_by_character_and_resource(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str
    ) -> CharacterResourceReadSchema | None:
        ...

class CharacterResourceRepository(CharacterResourceRepositoryProtocol):
    async def increment_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        increment: int
    ) -> bool:
        async with self.session as session, session.begin():
            # Попробуем обновить существующую запись
            stmt = (
                sa.update(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.resource_slug == resource_slug
                )
                .values(amount=self.model_type.amount + increment)
                .returning(self.model_type.id)  # чтобы понять, была ли запись
            )
            result = await session.execute(stmt)
            updated_row = result.fetchone()

            if updated_row:
                # Запись была обновлена
                return True

            # Если запись не найдена, создаём новую
            create_data = CharacterResourceCreateSchema(
                character_id=character_id,
                resource_slug=resource_slug,
                amount=increment
            )

            stmt = (
                sa.insert(self.model_type)
                .values(**create_data.model_dump(exclude={'id'}))
            )
            await session.execute(stmt)

            return True

    async def decrement_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        decrement: int
    ) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.resource_slug == resource_slug
                )
                .values(amount=self.model_type.amount - decrement)
                .returning(self.model_type.id)
            )
            result = await session.execute(stmt)
            updated_row = result.fetchone()

            return updated_row is not None

    async def get_by_character_and_resource(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str
    ) -> CharacterResourceReadSchema | None:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.resource_slug == resource_slug
                )
            )
            result = (await session.execute(stmt)).scalar_one_or_none()
            
            if result is None:
                return None
            
            return self.read_schema_type.model_validate(result, from_attributes=True)