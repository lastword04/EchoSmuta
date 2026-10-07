from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import CharacterDistributions
from ...schemas import CharacterDistributionsReadSchema, CharacterDistributionsCreateSchema, CharacterDistributionsUpdateSchema
from typing_extensions import Self
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid
from ...enums import CharacterSkillType
from datetime import datetime, timezone
from .....core.utils.exceptions import ModelFieldNotFoundException


class CharacterDistributionsRepositoryProtocol(BaseRepositoryImpl[
    CharacterDistributions,
    CharacterDistributionsReadSchema,
    CharacterDistributionsCreateSchema,
    CharacterDistributionsUpdateSchema
]):
    async def get_or_create_by_character_id(self: Self, character_id: uuid.UUID) -> list[CharacterDistributionsReadSchema]:
        ...

    async def get_by_character_id_and_skill_type(self: Self, character_id: uuid.UUID, skill_type: CharacterSkillType) -> Optional[CharacterDistributionsReadSchema]:
        ...

    async def reset_character_distribution(self: Self, character_id: uuid.UUID) -> bool:
        ...

class CharacterDistributionsRepository(CharacterDistributionsRepositoryProtocol):
    async def get_or_create_by_character_id(
    self: Self, 
    character_id: uuid.UUID
    ) -> list[CharacterDistributionsReadSchema]:
        """Get or create with race condition protection."""
        while True:
            async with self.session as s, s.begin():
                stmt = select(self.model_type).where(
                    self.model_type.character_id == character_id
                )
                result = await s.execute(stmt)
                distributions = result.scalars().all()
                
                if distributions:
                    return [
                        self.read_schema_type.model_validate(obj, from_attributes=True)
                        for obj in distributions
                    ]
                
                # Пытаемся создать
                default_distributions = [
                    {
                        "character_id": character_id,
                        "skill_type": CharacterSkillType.STANDARD,
                        "count_distributions": 0,
                        "price": 0
                    },
                    {
                        "character_id": character_id,
                        "skill_type": CharacterSkillType.MASTERSHIP,
                        "count_distributions": 0,
                        "price": 0
                    }
                ]
                
                try:
                    insert_stmt = sa.insert(self.model_type).returning(self.model_type)
                    new_models = (await s.scalars(insert_stmt, default_distributions)).all()
                    return [
                        self.read_schema_type.model_validate(model, from_attributes=True)
                        for model in new_models
                    ]
                except IntegrityError as e:
                    continue

    async def get_by_character_id_and_skill_type(self, character_id: uuid.UUID, skill_type: CharacterSkillType) -> Optional[CharacterDistributionsReadSchema]:
        async with self.session as session:
            stmt = select(CharacterDistributions).where(
                CharacterDistributions.character_id == character_id,
                CharacterDistributions.skill_type == skill_type
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
                    
            if record is None:
              raise ModelFieldNotFoundException(self.model_type, 'character_id', character_id)
            else:
              return CharacterDistributionsReadSchema.model_validate(record, from_attributes=True)
            
    async def reset_character_distribution(self, character_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(CharacterDistributions).where(
                    CharacterDistributions.character_id == character_id
                ).values(price=0, count_distributions=0)
            )
        
            try:
                result = await session.execute(stmt)                            
                row_count = result.rowcount
                return row_count > 0
            except Exception as e:
                print(f"An error occurred during reset: {e}")
                return False        