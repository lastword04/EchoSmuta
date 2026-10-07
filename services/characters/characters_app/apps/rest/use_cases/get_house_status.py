from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol


class GetHouseStatusUseCaseProtocol(UseCaseProtocol[dict]):
    async def __call__(self: Self, user: UserTokenDataReadSchema) -> dict: ...


class GetHouseStatusUseCase(GetHouseStatusUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema) -> dict:
        character = await self.character_repository.get(user.character_id)
        return await self.service.get_status(character)