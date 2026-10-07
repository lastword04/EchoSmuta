import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol
from ..schemas import HouseFurnitureItemSchema


class GetMyFurnitureUseCaseProtocol(UseCaseProtocol[list[HouseFurnitureItemSchema]]):
    async def __call__(self: Self, user: UserTokenDataReadSchema) -> list[HouseFurnitureItemSchema]:
        ...


class GetMyFurnitureUseCase(GetMyFurnitureUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema) -> list[HouseFurnitureItemSchema]:
        character = await self.character_repository.get(user.character_id)
        return await self.service.get_my_furniture(character)