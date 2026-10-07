import uuid
from typing import Protocol
from typing_extensions import Self
from ....core.utils.exceptions import ModelNotFoundException
from ..models import CharacterFastItem
from ..repositories.panels import CharacterFastItemRepositoryProtocol
from ..schemas  import(
    CharacterFastItemCreateDBSchema,
    CharacterFastItemUpdateSchema,
    CharacterFastItemUpdateDBSchema,
    CharacterFastItemReadSchema
)


class ItemsCRUServiceProtocol(Protocol):
    async def create(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        ...
    
    async def update(self: Self, items_id: uuid.UUID, data: CharacterFastItemUpdateSchema, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        ...

    async def get_for_character(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        ...
    
class ItemsCRUService(ItemsCRUServiceProtocol):
    def __init__(self: Self, repository: CharacterFastItemRepositoryProtocol):
        self.repository = repository
    
    async def create(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        db_notebook = CharacterFastItemCreateDBSchema(
            character_id=character_id,
        )
        return await self.repository.create(db_notebook)
    
    async def update(self: Self, items_id: uuid.UUID, data: CharacterFastItemUpdateSchema, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        items = await self.repository.get(items_id)
        if items.character_id != character_id:
            raise ModelNotFoundException(CharacterFastItem, items_id)
        db_notebook = CharacterFastItemUpdateDBSchema(
            **data.model_dump(exclude={"id"}),
            id=items_id,
            character_id=character_id,
        )
        return await self.repository.update(db_notebook)
    
    async def get_for_character(self: Self, character_id: uuid.UUID) -> CharacterFastItemReadSchema:
        return await self.repository.get_for_character(character_id)

