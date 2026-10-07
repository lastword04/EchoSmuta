from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import CharacterAbilitySkills
from ...schemas import CharacterAbilitySkillsReadSchema, CharacterAbilitySkillsCreateSchema, CharacterAbilitySkillsUpdateSchema
from typing_extensions import Self
from .....core.utils.exceptions import ModelFieldNotFoundException
import sqlalchemy as sa
import uuid


class CharacterAbilitySkillsRepositoryProtocol(BaseRepositoryImpl[
    CharacterAbilitySkills,
    CharacterAbilitySkillsReadSchema,
    CharacterAbilitySkillsCreateSchema,
    CharacterAbilitySkillsUpdateSchema
]):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        ...

class CharacterAbilitySkillsRepository(CharacterAbilitySkillsRepositoryProtocol):
    async def get_by_character_id(self: Self, character_id: uuid.UUID) -> CharacterAbilitySkillsReadSchema:
        async with self.session as session:
            stmt = sa.select(CharacterAbilitySkills).where(CharacterAbilitySkills.character_id == character_id)
            result = await session.execute(stmt)
            skills = result.scalar_one_or_none()
            if skills is None:
                raise ModelFieldNotFoundException(self.model_type, "character_id", character_id)
            return CharacterAbilitySkillsReadSchema.model_validate(skills, from_attributes=True)