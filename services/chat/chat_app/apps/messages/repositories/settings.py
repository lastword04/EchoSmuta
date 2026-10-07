import uuid
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from shared.schemas.chat import ChatSettingsReadSchema
from ..models import ChatSettings
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException, ModelNotFoundException, ModelAlreadyExistsError
from ..schemas import ChatSettingsCreateSchema, ChatSettingsUpdateDBSchema

class ChatSettingsRepositoryProtocol(BaseRepositoryImpl[ChatSettings, ChatSettingsReadSchema, ChatSettingsCreateSchema, ChatSettingsUpdateDBSchema]):
    async def get_by_character_id(self, character_id: uuid.UUID) -> ChatSettingsReadSchema:
        ...

    async def update_by_character_id(self, update_object: ChatSettingsUpdateDBSchema, character_id: uuid.UUID,) -> ChatSettingsReadSchema:
        ...

class ChatSettingsRepository(ChatSettingsRepositoryProtocol):
    async def get_by_character_id(self, character_id: uuid.UUID) -> ChatSettingsReadSchema:
        async with self.session as session:
            stmt = (
            sa.select(self.model_type)
            .where(self.model_type.character_id == character_id)
        )
            result = (await session.execute(stmt)).scalar_one_or_none()

            if not result:
                raise ModelFieldNotFoundException(self.model_type, "character_id", character_id)
            
            return ChatSettingsReadSchema.model_validate(result, from_attributes=True)

    async def update_by_character_id(self, update_object: ChatSettingsUpdateDBSchema, character_id: uuid.UUID) -> ChatSettingsReadSchema:
        async with self.session as s, s.begin():
            try:
                stmt = (
                    sa.update(self.model_type)
                    .where(self.model_type.character_id == character_id)
                    .values(**update_object.model_dump(exclude={"id", "character_id"}))
                    .returning(self.model_type)
                )

                model = (await s.execute(stmt)).scalar_one_or_none()
                if model is None:
                    raise ModelNotFoundException(self.model_type, update_object.id)

                return self.read_schema_type.model_validate(model, from_attributes=True)
            except IntegrityError as e:
                error_msg = str(e).lower()
                if "unique constraint" in error_msg or "duplicate key" in error_msg:
                    field_name = self._extract_duplicate_field(str(e))
                    raise ModelAlreadyExistsError(
                        model=self.model_type,
                        field=field_name,
                        message="duplicate key"
                    )
                raise
