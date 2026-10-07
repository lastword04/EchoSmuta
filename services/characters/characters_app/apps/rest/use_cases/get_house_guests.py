import uuid

from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..schemas import HouseGuestsResponseSchema
from ..services.house_guest_service import HouseGuestServiceProtocol


class GetHouseGuestsUseCaseProtocol(UseCaseProtocol[HouseGuestsResponseSchema]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID) -> HouseGuestsResponseSchema:
        ...


class GetHouseGuestsUseCase(GetHouseGuestsUseCaseProtocol):
    def __init__(self: Self, service: HouseGuestServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema, house_id: uuid.UUID) -> HouseGuestsResponseSchema:
        character = await self.character_repository.get(user.character_id)
        return await self.service.get_guests(character, house_id)