import uuid
import sqlalchemy as sa
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import FavoriteBells
from ..schemas import FavoriteBellsCreateSchema, FavoriteBellsUpdateDBSchema, FavoriteBellsReadSchema

class FavoriteBellsRepositoryProtocol(BaseRepositoryImpl[
    FavoriteBells,
    FavoriteBellsReadSchema,
    FavoriteBellsCreateSchema,
    FavoriteBellsUpdateDBSchema
]):
    async def get_all_for_character(self: Self, character_id: uuid.UUID) -> list[FavoriteBellsReadSchema]:
        ...

    async def delete(self: Self, character_id: uuid.UUID, code_bell: int) -> bool:
        ...

class FavoriteBellsRepository(FavoriteBellsRepositoryProtocol):
    async def get_all_for_character(self: Self, character_id: uuid.UUID) -> list[FavoriteBellsReadSchema]:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
            )

            result = await session.execute(stmt)

            favorite_bells = [self.read_schema_type.model_validate(row[0], from_attributes=True)
                               for row in result.fetchall()]

            return favorite_bells
        
    async def delete(self: Self, character_id: uuid.UUID, code_bell: int) -> bool:
        async with self.session as session:
            stmt = (
                sa.delete(self.model_type)
                .where(self.model_type.character_id == character_id,
                       self.model_type.code_bell == code_bell
                )

            )

            await session.execute(stmt)
            return True
