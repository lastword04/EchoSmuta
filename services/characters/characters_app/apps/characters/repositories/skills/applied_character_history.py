from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import AppliedCharacterHistory
from ...schemas import AppliedCharacterHistoryReadSchema, AppliedCharacterHistoryCreateSchema, AppliedCharacterHistoryUpdateSchema
from typing_extensions import Self
from sqlalchemy.exc import IntegrityError
from .....core.utils.exceptions import ModelNotFoundException, ModelAlreadyExistsError, ModelFieldNotFoundException
import sqlalchemy as sa
import uuid


class AppliedCharacterHistoryRepositoryProtocol(BaseRepositoryImpl[
    AppliedCharacterHistory,
    AppliedCharacterHistoryReadSchema,
    AppliedCharacterHistoryCreateSchema,
    AppliedCharacterHistoryUpdateSchema
]):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        ...

    async def update_by_character_id(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryUpdateSchema:
        ...
    
class AppliedCharacterHistoryRepository(AppliedCharacterHistoryRepositoryProtocol):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> AppliedCharacterHistoryReadSchema:
        async with self.session as session:
            stmt = sa.select(AppliedCharacterHistory).where(AppliedCharacterHistory.character_id == character_id)
            result = await session.execute(stmt)
            skills = result.scalar_one_or_none()
            if skills is None:
                raise ModelFieldNotFoundException(self.model_type, "character_id", character_id)
            return AppliedCharacterHistoryReadSchema.model_validate(skills, from_attributes=True)
        
    async def update_by_character_id(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryUpdateSchema) -> AppliedCharacterHistoryReadSchema:
        try:
            async with self.session as session, session.begin():
            # Обновляем запись, применяя фильтр по character_id
                statement = (
                    sa.update(self.model_type)
                    .where(self.model_type.character_id == data.character_id)
                    .values(data.model_dump(exclude={'character_id', 'id'}, exclude_unset=False))  # Исключаем неизменяемое поле character_id
                    .returning(self.model_type)
            )
            
                result = await session.execute(statement)
                updated_model = result.scalar_one_or_none()
            
            if updated_model is None:
                raise ModelNotFoundException(self.model_type, data.character_id)
                
            return self.read_schema_type.model_validate(updated_model, from_attributes=True)
        except IntegrityError as e:
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                field_name = self._extract_field_name(str(e), type(data))
                raise ModelAlreadyExistsError(self.model_type, field_name, f"duplicate key for field: {field_name}")
            else:
                raise