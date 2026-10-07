from typing import Protocol

from shared.schemas.base import StatusOkSchema

from ...schemas import BuildingCreateSchema
from ...services.building.building import BuildingServiceProtocol


class InitializeBuildingsUseCaseProtocol(Protocol):
    async def __call__(self) -> StatusOkSchema:
        ...


class InitializeBuildingsUseCase(InitializeBuildingsUseCaseProtocol):
    def __init__(self, service: BuildingServiceProtocol):
        self.service = service

    async def __call__(self) -> StatusOkSchema:
        buildings_data = [
            BuildingCreateSchema(
                location_slug="1.35.laboratory",
                city_trading_location_slug="1.9.pharmacy"
            ),
            BuildingCreateSchema(
                location_slug="1.36.kitchen",
                city_trading_location_slug="1.25.fish-shop"
            ),
            BuildingCreateSchema(
                location_slug="1.37.carpentry-workshop",
                city_trading_location_slug="1.21.furniture-shop"
            ),
            BuildingCreateSchema(
                location_slug="1.39.incubator",
                city_trading_location_slug="1.24.bird-market"
            ),
            BuildingCreateSchema(
                location_slug="1.38.hunter-workshop",
                city_trading_location_slug="1.22.hunting-shop"
            ),
            BuildingCreateSchema(
                location_slug="1.13.forge",
                city_trading_location_slug="1.13.forge"
            ),
            BuildingCreateSchema(
                location_slug="1.16.jewelers",
                city_trading_location_slug="1.16.jewelers"
            ),
        ]

        existing_slugs = {building.location_slug for building in await self.service.get_all()}
        for building_data in buildings_data:
            if building_data.location_slug not in existing_slugs:
                await self.service.create(building_data)

        return StatusOkSchema()
