import uuid

import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelNotFoundException
from ...models import CharacterStartCreatingItem
from ...schemas import (
    CharacterStartCreatingItemCreateSchema,
    CharacterStartCreatingItemReadSchema,
    CharacterStartCreatingItemUpdateSchema,
)


class CharacterStartCreatingItemRepositoryProtocol(
    BaseRepositoryImpl[
        CharacterStartCreatingItem,
        CharacterStartCreatingItemReadSchema,
        CharacterStartCreatingItemCreateSchema,
        CharacterStartCreatingItemUpdateSchema
    ]
):
    async def update_craft_stage(
        self, start_creating_id: uuid.UUID, craft_stage: int
    ) -> CharacterStartCreatingItemReadSchema:
        """Обновляет стадию крафта."""

    async def get_all_by_character(
        self, character_id: uuid.UUID
    ) -> list[CharacterStartCreatingItemReadSchema]:
        """Получает все записи крафта для персонажа."""

    async def get_by_character_and_item(
        self, character_id: uuid.UUID, item_slug: str
    ) -> CharacterStartCreatingItemReadSchema | None:
        ...


class CharacterStartCreatingItemRepository(CharacterStartCreatingItemRepositoryProtocol):
    async def update_craft_stage(
        self, start_creating_id: uuid.UUID, craft_stage: int
    ) -> CharacterStartCreatingItemReadSchema:
        """Обновляет стадию крафта."""
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(
                    self.model_type.id == start_creating_id,
                )
                .values(craft_stage=craft_stage)
                .returning(self.model_type)
            )
            
            model = (await session.execute(stmt)).scalar_one_or_none()
            
            if model is None:
                raise ModelNotFoundException(self.model_type, start_creating_id)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def get_all_by_character(
        self, character_id: uuid.UUID
    ) -> list[CharacterStartCreatingItemReadSchema]:
        """Получает все записи крафта для персонажа."""
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
            )
            models = (await session.execute(stmt)).scalars().all()
            return [
                self.read_schema_type.model_validate(m, from_attributes=True)
                for m in models
            ]

    async def get_by_character_and_item(
        self, character_id: uuid.UUID, item_slug: str
    ) -> CharacterStartCreatingItemReadSchema | None:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.item_slug == item_slug,
                )
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                return None
            return self.read_schema_type.model_validate(model, from_attributes=True)
