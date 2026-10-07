from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CharacterRecipeWithStockSchema
from ...services.crafting.character_start_creating_item import (
    CharacterStartCreatingItemServiceProtocol,
)
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class GetCharacterCreatingItemsUseCaseProtocol(UseCaseProtocol[list[CharacterRecipeWithStockSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeWithStockSchema]:
        ...


class GetCharacterCreatingItemsUseCase(GetCharacterCreatingItemsUseCaseProtocol):
    def __init__(
        self: Self,
        crafting_service: CharacterStartCreatingItemServiceProtocol,
        recipes_service: CharacterRecipesServiceProtocol
    ):
        self.crafting_service = crafting_service
        self.recipes_service = recipes_service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeWithStockSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.recipes_service.get_character_creating_items_with_stock(token.character_id)
