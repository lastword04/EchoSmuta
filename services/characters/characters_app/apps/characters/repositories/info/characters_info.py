import uuid
from typing import Sequence
from typing_extensions import Self
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from shared.schemas.characters import CharacterListIds
from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException, ModelNotFoundException, ModelAlreadyExistsError
from ...models import CharacterInfo
from ...schemas import CharacterInfoCreateSchema, CharacterInfoUpdateDBSchema, CharacterInfoReadSchema

class CharacterInfoRepositoryProtocol(BaseRepositoryImpl[
    CharacterInfo,
    CharacterInfoReadSchema,
    CharacterInfoCreateSchema,
    CharacterInfoUpdateDBSchema
]):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        ...
    async def update_by_character_id(self: Self, character_info: CharacterInfoUpdateDBSchema, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        ...

    async def get_by_ids(self: Self, ids: Sequence[uuid.UUID]) -> list[CharacterInfoReadSchema]:
        ...

    async def update_location_slug_by_character(self: Self, character_id: uuid.UUID, location_slug: str) -> None:
        ...

class CharacterInfoRepository(CharacterInfoRepositoryProtocol):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "character_id", character_id)

            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def update_by_character_id(self: Self, character_info: CharacterInfoUpdateDBSchema, character_id: uuid.UUID) -> CharacterInfoReadSchema:
        async with self.session as session, session.begin():
            try:
                stmt = (
                    sa.update(self.model_type)
                    .where(self.model_type.character_id == character_id)
                    .values(character_info.model_dump(exclude={"id", "character_id"}))
                    .returning(self.model_type)
                )

                model = (await session.execute(stmt)).scalar_one_or_none()
                if model is None:
                    raise ModelNotFoundException(self.model_type, character_info.id)

                return self.read_schema_type.model_validate(model, from_attributes=True)
            except IntegrityError as e:
                if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                    field_name = self._extract_field_name(str(e), type(character_info))
                    raise ModelAlreadyExistsError(self.model_type, field_name, f"duplicate key for field: {field_name}")

                raise
    
    

            
