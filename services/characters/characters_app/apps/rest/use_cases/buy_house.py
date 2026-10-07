from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ...characters.repositories.character.characters import CharacterRepositoryProtocol
from ..services.house_service import HouseServiceProtocol


class BuyHouseUseCaseProtocol(UseCaseProtocol[dict]):
    async def __call__(self: Self, user: UserTokenDataReadSchema) -> dict: ...


class BuyHouseUseCase(BuyHouseUseCaseProtocol):
    def __init__(self: Self, service: HouseServiceProtocol, character_repository: CharacterRepositoryProtocol):
        self.service = service
        self.character_repository = character_repository

    async def __call__(self: Self, user: UserTokenDataReadSchema) -> dict:
        character = await self.character_repository.get(user.character_id)
        house = await self.service.buy_house(character)
        return {
            "id": house.id,
            "number": house.number,
            "capacity": house.capacity,
            "current_volume": house.current_volume,
            "bonuses": {
                stat: round((mult - 1.0) * 100)
                for stat, mult in (house.regen_multipliers or {}).items()
            },
        }