from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.locations.locations_stats import LocationsStatsServiceProtocol 
from ...schemas import LocationCharacterCountSchema

class CountCharactersByLocationUseCaseProtocol(UseCaseProtocol[list[LocationCharacterCountSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[LocationCharacterCountSchema]:
        ...


class CountCharactersByLocationUseCase(CountCharactersByLocationUseCaseProtocol):
    def __init__(self: Self, service: LocationsStatsServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[LocationCharacterCountSchema]:
        return await self.service.get_character_counts_by_location()
