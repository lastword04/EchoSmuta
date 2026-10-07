from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import ResourceItemReadSchema
from ...services.recipes.character_recipes import CharacterRecipesServiceProtocol


class GetAllRecipesUseCaseProtocol(UseCaseProtocol[list[ResourceItemReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, quantity: int) -> list[ResourceItemReadSchema]:
        ...


class GetAllRecipesUseCase(GetAllRecipesUseCaseProtocol):
    def __init__(self: Self, service: CharacterRecipesServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema, quantity: int) -> list[ResourceItemReadSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_all_recipes(token.character_id, quantity)