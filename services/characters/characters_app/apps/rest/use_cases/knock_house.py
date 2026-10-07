import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_guest_service import HouseGuestServiceProtocol


class KnockHouseUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID) -> None:
        ...


class KnockHouseUseCase(KnockHouseUseCaseProtocol):
    def __init__(self: Self, service: HouseGuestServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, house_number: int) -> None:
        character = await self.character_repository.get(user.character_id)
        await self.service.knock(character, house_number)