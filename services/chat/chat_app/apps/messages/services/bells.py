import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.bells import FavoriteBellsRepositoryProtocol
from ..schemas import (
    FavoriteBellsCreateSchema, FavoriteBellsReadSchema,
    FavoriteBellsRequestSchema
)

class FavoriteBellsServiceProtocol(Protocol):
    async def create(self: Self, favorite_bells: FavoriteBellsRequestSchema, character_id: uuid.UUID) -> FavoriteBellsReadSchema:
        ...

    async def delete(self: Self, character_id: uuid.UUID, code_bell: int) -> bool:
        ...

    async def get_all_favorite_for_character(self: Self, character_id: uuid.UUID) -> list[FavoriteBellsReadSchema]:
        ...

class FavoriteBellsService(FavoriteBellsServiceProtocol):
    def __init__(self: Self, repository: FavoriteBellsRepositoryProtocol):
        self.repository = repository

    async def create(self: Self, favorite_bells: FavoriteBellsRequestSchema, character_id: uuid.UUID) -> FavoriteBellsReadSchema:
        create_schema = FavoriteBellsCreateSchema(
            character_id=character_id,
            **favorite_bells.model_dump()
        )
        return await self.repository.create(create_schema)
    
    async def delete(self: Self, character_id: uuid.UUID, code_bell: int) -> bool:
        return await self.repository.delete(character_id, code_bell)


    async def get_all_favorite_for_character(self: Self, character_id: uuid.UUID) -> list[FavoriteBellsReadSchema]:
        return await self.repository.get_all_for_character(character_id)