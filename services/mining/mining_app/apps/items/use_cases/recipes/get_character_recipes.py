from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CharacterRecipeReadSchema
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class GetCharacterRecipesUseCaseProtocol(UseCaseProtocol[list[CharacterRecipeReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeReadSchema]:
        ...


class GetCharacterRecipesUseCase(GetCharacterRecipesUseCaseProtocol):
    def __init__(self: Self, service: CharacterRecipesServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterRecipeReadSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_character_recipes(token.character_id)
