from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationSettingsCreateSchema, LocationSettingsReadSchema
from ...services.location_settings import LocationSettingsServiceProtocol


class InitializeLocationSettingsUseCaseProtocol(UseCaseProtocol[list[LocationSettingsReadSchema]]):
    async def __call__(self: Self) -> list[LocationSettingsReadSchema]:
        ...


class InitializeLocationSettingsUseCase(InitializeLocationSettingsUseCaseProtocol):
    def __init__(self: Self, service: LocationSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[LocationSettingsReadSchema]:

        used_locations = await self.service.get_all()
        default_locations = self._get_default_experiences(2)
        if len(used_locations) == len(default_locations):
            return used_locations
        if len(used_locations) != 0:
            raise ValueError("Locations not corrected count.")

        return await self.service.bulk_create(default_locations)

    def _get_default_experiences(self: Self, city_number: int) -> list[LocationSettingsCreateSchema]:
        return [
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.1.swamp",
                up_chance_for_unluck=0.03
            ),
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.4.lake",
                up_chance_for_unluck=0.03
            ),
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.5.forest",
                up_chance_for_unluck=0.03
            ),
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.2.shaft",
                up_chance_for_unluck=0.03
            ),
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.3.mine",
                up_chance_for_unluck=0.03
            ),
            LocationSettingsCreateSchema(
                location_slug=f"{city_number}.6.sands",
                up_chance_for_unluck=0.03
            )
        ]
    