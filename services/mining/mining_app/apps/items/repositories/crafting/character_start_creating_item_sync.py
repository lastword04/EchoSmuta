import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelNotFoundException
from ...models import CharacterStartCreatingItem
from ...schemas import (
    CharacterStartCreatingItemCreateSchema,
    CharacterStartCreatingItemReadSchema,
)


class CharacterStartCreatingItemSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model_type = CharacterStartCreatingItem
        self.read_schema_type = CharacterStartCreatingItemReadSchema

    def update_craft_stage(
        self, start_creating_id: uuid.UUID, craft_stage: int
    ) -> CharacterStartCreatingItemReadSchema:
        stmt = (
            sa.update(self.model_type)
            .where(self.model_type.id == start_creating_id)
            .values(craft_stage=craft_stage)
            .returning(self.model_type)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ModelNotFoundException(self.model_type, start_creating_id)
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def get_all_by_character(
        self, character_id: uuid.UUID
    ) -> list[CharacterStartCreatingItemReadSchema]:
        stmt = sa.select(self.model_type).where(
            self.model_type.character_id == character_id
        )
        models = self.session.execute(stmt).scalars().all()
        return [
            self.read_schema_type.model_validate(m, from_attributes=True)
            for m in models
        ]

    def get(self, start_creating_id: uuid.UUID) -> CharacterStartCreatingItemReadSchema:
        model = self.session.get(self.model_type, start_creating_id)
        if model is None:
            raise ModelNotFoundException(self.model_type, start_creating_id)
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def get_by_character_and_item(
        self, character_id: uuid.UUID, item_slug: str
    ) -> CharacterStartCreatingItemReadSchema | None:
        stmt = sa.select(self.model_type).where(
            self.model_type.character_id == character_id,
            self.model_type.item_slug == item_slug,
        )
        model = self.session.execute(stmt).scalars().first()
        if model is None:
            return None
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def create(self, data: CharacterStartCreatingItemCreateSchema) -> CharacterStartCreatingItemReadSchema:
        model = self.model_type(
            character_id=data.character_id,
            item_slug=data.item_slug,
            craft_stage=data.craft_stage,
        )
        self.session.add(model)
        self.session.flush()
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def delete(self, start_creating_id: uuid.UUID) -> None:
        stmt = sa.delete(self.model_type).where(self.model_type.id == start_creating_id)
        self.session.execute(stmt)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()