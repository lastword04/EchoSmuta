from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...schemas import CityCreateSchema, CityReadSchema
from ...services.cities.cities import CityServiceProtocol 


class InitializeCitiesUseCaseProtocol(UseCaseProtocol[list[CityReadSchema]]):
    async def __call__(self: Self) -> list[CityReadSchema]:
        ...


class InitializeCitiesUseCase(InitializeCitiesUseCaseProtocol):
    def __init__(self: Self, service: CityServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[CityReadSchema]:
         
        used_cities = await self.service.get_all()
        default_cities = self._get_default_cities()
        if len(used_cities) == len(default_cities):
            return used_cities
        if len(used_cities) != 0:
            raise ValueError("Cities not corrected count.")
        
        return await self.service.bulk_create(default_cities)

    def _get_default_cities(self: Self) -> list[CityCreateSchema]:
        return [
            CityCreateSchema(name="Авалон", serial_number=1),
            # Окрестности Авалона 2
            CityCreateSchema(name="Альбинар", serial_number=3)
        ]