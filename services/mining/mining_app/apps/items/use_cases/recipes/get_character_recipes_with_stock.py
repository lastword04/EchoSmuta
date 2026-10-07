from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CharacterRecipeWithStockSchema
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class GetCharacterRecipesWithStockUseCaseProtocol(UseCaseProtocol[list[CharacterRecipeWithStockSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> list[CharacterRecipeWithStockSchema]:
        ...


class GetCharacterRecipesWithStockUseCase(GetCharacterRecipesWithStockUseCaseProtocol):
    def __init__(self: Self, service: CharacterRecipesServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> list[CharacterRecipeWithStockSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_character_recipes_with_stock(token.character_id, location_slug)
