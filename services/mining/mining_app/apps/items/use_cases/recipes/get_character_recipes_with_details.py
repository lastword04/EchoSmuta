from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CharacterRecipeWithDetailsSchema
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class GetCharacterRecipesWithDetailsUseCaseProtocol(UseCaseProtocol[list[CharacterRecipeWithDetailsSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeWithDetailsSchema]:
        ...


class GetCharacterRecipesWithDetailsUseCase(GetCharacterRecipesWithDetailsUseCaseProtocol):
    def __init__(self: Self, service: CharacterRecipesServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeWithDetailsSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_character_recipes_with_details(token.character_id)
