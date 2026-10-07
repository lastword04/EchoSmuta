from typing_extensions import Self
from shared.schemas.locations import LocationReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.locations.locations import LocationServiceProtocol 

class GetLocationBySlugUseCaseProtocol(UseCaseProtocol[LocationReadSchema]):
    async def __call__(self: Self, slug: str) -> LocationReadSchema:
        ...


class GetLocationBySlugUseCase(GetLocationBySlugUseCaseProtocol):
    def __init__(self: Self, service: LocationServiceProtocol):
        self.service = service

    async def __call__(self: Self, slug: str) -> LocationReadSchema:
        return await self.service.get_by_slug(slug)
