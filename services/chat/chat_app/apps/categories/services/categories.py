import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from shared.schemas.category import BaseCategoryStatsSchema
from ..repositories.categories import CategoryRepositoryProtocol
from ..schemas import (
    CategoryCreateSchema, CategoryReadSchema, 
    CategoryCreateDBSchema, CategoryWithCharacterCountSchema,
    CategoryUpdateCheckbox
)
from ..exceptions import CategoryLimitExceededError

class CategoryServiceProtocol(Protocol):
    async def can_create_category(self: Self, character_id: uuid.UUID, max_categories: int) -> bool:
        ...
        
    async def create(self: Self, category: CategoryCreateSchema, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        ...

    async def delete(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        ...

    async def create_default(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        ...
    
    async def get_all_by_character_id(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        ...

    async def get_all_by_character_id_with_character_count(self: Self, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        ...

    async def calculate_stats_base_category(self: Self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        ...

    async def update_checkbox_fields(
        self: Self, 
        category_id: uuid.UUID, 
        character_id: uuid.UUID,
        update_data: CategoryUpdateCheckbox
    ) -> CategoryReadSchema:
        ...

class CategoryService(CategoryServiceProtocol):
    def __init__(self: Self, repository: CategoryRepositoryProtocol,
                 max_categories: int = 5,
                 main_max_count_characters: int = 30,
                 not_main_max_count_characters: int = 20):
        self.repository = repository
        self.max_categories = max_categories
        self.main_max_count_characters = main_max_count_characters
        self.not_main_max_count_characters = not_main_max_count_characters

    async def can_create_category(self: Self, character_id: uuid.UUID, max_categories: Optional[int] = None) -> bool:
        valid_max_categories = max_categories or self.max_categories 
        categories = await self.get_all_by_character_id(character_id)
        return len(categories) < valid_max_categories

    async def create(self: Self, category: CategoryCreateSchema, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        if not (await self.can_create_category(character_id, self.max_categories)):
            raise CategoryLimitExceededError(character_id, self.max_categories)
        
        category_create = CategoryCreateDBSchema(
            **category.model_dump(),
            owner_character_id=character_id,
            is_main=False,
            max_count_characters=self.not_main_max_count_characters,
            is_send_notifications=None,
            is_receive_notifications=None,
            is_block_send_mails=False
        )
        
        await self.repository.create(category_create)
    
        return await self.get_all_by_character_id_with_character_count(character_id)
    
    async def get_all_by_character_id(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        return await self.repository.get_all_by_character_id(character_id)
    
    async def get_all_by_character_id_with_character_count(self: Self, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        return await self.repository.get_all_by_character_id_with_character_count(character_id)
    
    async def delete(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        return await self.repository.delete(category_id, character_id)
    
    async def update_checkbox_fields(
        self: Self, 
        category_id: uuid.UUID, 
        character_id: uuid.UUID,
        update_data: CategoryUpdateCheckbox
    ) -> list[CategoryWithCharacterCountSchema]:
        await self.repository.update_checkbox_fields(category_id, character_id, update_data)
        return await self.get_all_by_character_id_with_character_count(character_id)

    async def calculate_stats_base_category(self: Self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        return await self.repository.calculate_stats_base_category(character_id)

    async def create_default(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        categories = self._get_default_categories(character_id)
        return await self.repository.bulk_create(categories)

    def _get_default_categories(self: Self, character_id: uuid.UUID) -> list[CategoryCreateDBSchema]:
        return [
            CategoryCreateDBSchema(
                name="Друзья",
                owner_character_id=character_id,
                is_main=True,
                max_count_characters=self.main_max_count_characters,
                is_send_notifications=False,
                is_receive_notifications=False,
                is_block_send_mails=False
            ),
            CategoryCreateDBSchema(
                name="Враги",
                owner_character_id=character_id,
                is_main=True,
                max_count_characters=self.main_max_count_characters,
                is_send_notifications=False,
                is_receive_notifications=False,
                is_block_send_mails=False
            ),
        ]
 
class CategoryCheckerMessageServiceProtocol(Protocol):
    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        ...

class CategoryCheckerMessageService(CategoryCheckerMessageServiceProtocol):
    def __init__(self: Self, repository: CategoryRepositoryProtocol):
        self.repository = repository

    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        return await self.repository.can_visible_notifications(owner_character_id, target_character_id)
