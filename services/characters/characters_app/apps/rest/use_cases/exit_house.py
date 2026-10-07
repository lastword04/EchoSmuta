from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol


class ExitHouseUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, user: UserTokenDataReadSchema) -> None: ...


class ExitHouseUseCase(ExitHouseUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema) -> None:
        character = await self.character_repository.get(user.character_id)
        await self.service.exit_house(character)