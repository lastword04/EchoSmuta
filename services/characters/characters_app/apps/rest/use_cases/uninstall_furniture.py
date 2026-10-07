import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol
from ..schemas import FurnitureMoveResponseSchema


class UninstallFurnitureUseCaseProtocol(UseCaseProtocol[FurnitureMoveResponseSchema]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, inventory_item_id: uuid.UUID) -> FurnitureMoveResponseSchema:
        ...


class UninstallFurnitureUseCase(UninstallFurnitureUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, inventory_item_id: uuid.UUID) -> FurnitureMoveResponseSchema:
        character = await self.character_repository.get(user.character_id)
        return await self.service.uninstall_furniture(character, inventory_item_id)