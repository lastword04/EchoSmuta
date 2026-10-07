import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import CharacterResource
from ..schemas import CharacterResourceReadSchema


class CharacterResourceSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_character_and_resource(
        self,
        character_id: uuid.UUID,
        resource_slug: str
    ) -> CharacterResourceReadSchema | None:
        stmt = sa.select(CharacterResource).where(
            CharacterResource.character_id == character_id,
            CharacterResource.resource_slug == resource_slug
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return CharacterResourceReadSchema.model_validate(model, from_attributes=True)

    def decrement_amount(
        self,
        character_id: uuid.UUID,
        resource_slug: str,
        decrement: int
    ) -> bool:
        stmt = (
            sa.update(CharacterResource)
            .where(
                CharacterResource.character_id == character_id,
                CharacterResource.resource_slug == resource_slug
            )
            .values(amount=CharacterResource.amount - decrement)
            .returning(CharacterResource.id)
        )
        result = self.session.execute(stmt)
        updated_row = result.fetchone()
        return updated_row is not None

    def increment_amount(
        self,
        character_id: uuid.UUID,
        resource_slug: str,
        increment: int
    ) -> bool:
        stmt = (
            sa.update(CharacterResource)
            .where(
                CharacterResource.character_id == character_id,
                CharacterResource.resource_slug == resource_slug
            )
            .values(amount=CharacterResource.amount + increment)
            .returning(CharacterResource.id)
        )
        result = self.session.execute(stmt)
        updated_row = result.fetchone()
        if updated_row:
            return True
        # если записи не было – создаём новую
        stmt_insert = sa.insert(CharacterResource).values(
            character_id=character_id,
            resource_slug=resource_slug,
            amount=increment
        )
        self.session.execute(stmt_insert)
        return True

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()