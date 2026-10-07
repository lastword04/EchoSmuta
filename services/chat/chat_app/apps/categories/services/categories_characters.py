import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.characters import (
    CharacterListIds
)
from ..adapter.characters import CharacterServiceClientProtocol
from ..repositories.categories_characters import CategoryCharacterRepositoryProtocol
from ..schemas import CategoryWithCharactersReadSchema
from ..exceptions import CannotAddSelfToCategoryError


class CategoryCharacterServiceProtocol(Protocol):
    async def get_by_category_id(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        ...

    async def add_by_character_name_to_category(self: Self, category_id: uuid.UUID, character_name: str, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        ...

    async def add_character_to_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        ...
    
    async def delete_character_from_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        ...

class CategoryCharacterService(CategoryCharacterServiceProtocol):
    def __init__(self: Self, category_character_repository: CategoryCharacterRepositoryProtocol,
                 character_service: CharacterServiceClientProtocol):
        self.category_character_repository = category_character_repository
        self.character_service = character_service

    async def get_by_category_id(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        categories = await self.category_character_repository.get_by_category_id(category_id, character_id)
        characters_ids = categories.characters_ids
        characters_data = await self.character_service.get_simple_info_by_ids(CharacterListIds(ids=characters_ids), is_online) if characters_ids else []
        return CategoryWithCharactersReadSchema(
            id=categories.id,
            name=categories.name,
            characters=characters_data.characters if characters_data else []
        )
    
    async def add_by_character_name_to_category(self: Self, category_id: uuid.UUID, character_name: str, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        character = await self.character_service.get_by_name(character_name)
        return await self.add_character_to_category(category_id, character.id, owner_character_id, is_online)
    
    async def add_character_to_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        await self.category_character_repository.add_character_to_category(category_id, character_id, owner_character_id)
        return await self.get_by_category_id(category_id, owner_character_id, is_online)
    
    async def delete_character_from_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID, is_online: Optional[bool] = None) -> CategoryWithCharactersReadSchema:
        await self.category_character_repository.delete_character_from_category(category_id, character_id, owner_character_id)
        return await self.get_by_category_id(category_id, owner_character_id, is_online)
    