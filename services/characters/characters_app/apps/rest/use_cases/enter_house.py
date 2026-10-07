import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol


class EnterHouseUseCaseProtocol(UseCaseProtocol[dict]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID) -> dict: ...


class EnterHouseUseCase(EnterHouseUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID) -> dict:
        character = await self.character_repository.get(user.character_id)
        return await self.service.enter_house(character, house_id)