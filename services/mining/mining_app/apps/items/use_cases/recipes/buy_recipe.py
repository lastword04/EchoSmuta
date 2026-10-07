from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CharacterRecipeCreateSchema, CharacterRecipeReadSchema
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class BuyRecipeUseCaseProtocol(UseCaseProtocol[CharacterRecipeReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, data: CharacterRecipeCreateSchema) -> CharacterRecipeReadSchema:
        ...


class BuyRecipeUseCase(BuyRecipeUseCaseProtocol):
    def __init__(self: Self, service: CharacterRecipesServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema, data: CharacterRecipeCreateSchema) -> CharacterRecipeReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.buy_recipe(token.character_id, data.item_slug, data.quantity)
