import uuid
from typing_extensions import Self
from shared.schemas.locations import LocationReadSchema
from shared.enums import LocationType
from .....core.use_cases import UseCaseProtocol 
from ...schemas import LocationCreateSchema
from ...services.locations.locations import LocationServiceProtocol 
from ...services.cities.cities import CityServiceProtocol

class InitializeLocationsUseCaseProtocol(UseCaseProtocol[list[LocationReadSchema]]):
    async def __call__(self: Self) -> list[LocationReadSchema]:
        ...


class InitializeLocationsUseCase(InitializeLocationsUseCaseProtocol):
    def __init__(self: Self, service: LocationServiceProtocol, city_service: CityServiceProtocol):
        self.service = service
        self.city_service = city_service

    async def __call__(self: Self) -> list[LocationReadSchema]:
        avalon = await self.city_service.get_by_name("Авалон")
        used_locations = await self.service.get_all()
        default_locations = self._get_default_locations(avalon.id, avalon.serial_number)
        if len(used_locations) == len(default_locations):
            return used_locations
        if len(used_locations) != 0:
            raise ValueError("Locations not corrected count.")
        
        return await self.service.bulk_create(default_locations)

    def _get_default_locations(self: Self, city_id: uuid.UUID, city_number: int) -> list[LocationCreateSchema]:
        location_data_neighborhood = [
            ("Болото", "swamp", LocationType.RESOURCES),
            ("Шахта", "shaft", LocationType.RESOURCES),
            ("Прииск", "mine", LocationType.RESOURCES),
            ("Озеро", "lake", LocationType.RESOURCES),
            ("Лес", "forest", LocationType.RESOURCES),
            ("Пески", "sands", LocationType.RESOURCES),
        ]

        location_data_city = [
            ("Академия", "academy", LocationType.OTHER),
            ("Арена Людей", "arena-humans", LocationType.OTHER),
            ("Арена Орков", "arena-orcs", LocationType.OTHER),
            ("Арена Раздора", "arena-chaos", LocationType.OTHER),
            ("Арена Эльфов", "arena-elves", LocationType.OTHER),
            ("Дворец", "palace", LocationType.OTHER),
            ("Дворец бракосочетаний", "wedding-palace", LocationType.OTHER),
            ("Храм", "temple", LocationType.OTHER),
            ("Аптека", "pharmacy", LocationType.ITEMS),
            ("Больница", "hospital", LocationType.OTHER),
            ("Вход в Лабиринт", "labyrinth-entrance", LocationType.OTHER),
            ("Гостиница", "inn", LocationType.REST),
            ("Кузница", "forge", LocationType.OTHER),
            ("Ремонтная Мастерская", "repair-shop", LocationType.OTHER),
            ("Харчевня", "tavern", LocationType.OTHER),
            ("Ювелиры", "jewelers", LocationType.OTHER),
            ("Вокзал", "station", LocationType.OTHER),
            ("Тюрьма", "prison", LocationType.OTHER),
            ("Частные дома", "residential-area", LocationType.REST),
            ("Магазин", "shop", LocationType.OTHER),
            ("Мебельная Лавка", "furniture-shop", LocationType.ITEMS),
            ("Охотничья Лавка", "hunting-shop", LocationType.ITEMS),
            ("Подарочный Магазин", "gift-shop", LocationType.OTHER),
            ("Питомник", "bird-market", LocationType.ITEMS),
            ("Рыбная Лавка", "fish-shop", LocationType.ITEMS),
            ("Скупочный Магазин", "pawn-shop", LocationType.OTHER),
            ("Торговая Палата", "trade-hall", LocationType.OTHER),
            ("Авалон", "avalon", LocationType.OTHER),
            ("Пещера Стонов", "cave-of-stones", LocationType.OTHER),
            ("Портал", "portal", LocationType.OTHER),
            ("Замок с Привидениями", "castle-of-ghosts", LocationType.OTHER),
            ("Замок Стали", "castle-of-steel", LocationType.OTHER),
            ("Замок Белого Камня", "castle-of-white-stone", LocationType.OTHER),
            ("Замок Ветра", "castle-of-wind", LocationType.OTHER),
            ("Лаборатория", "laboratory", LocationType.ITEMS),
            ("Кухня", "kitchen", LocationType.ITEMS),
            ("Столярная мастерская", "carpentry-workshop", LocationType.ITEMS),
            ("Мастерская охотника", "hunter-workshop", LocationType.ITEMS),
            ("Инкубатор", "incubator", LocationType.ITEMS),
        ]

        locations_schemas = []

        # Init Avalon
        for idx, location in enumerate(location_data_city):
            location_name, location_slug, location_type = location
            location_number = idx + 1
            location_schema = LocationCreateSchema(
                name=location_name,
                slug=f"{city_number}.{location_number}.{location_slug}",
                city_id=city_id,
                type=location_type,
                serial_number=location_number
            )
            locations_schemas.append(location_schema)

        neighborhood_number = city_number + 1
        for idx, location in enumerate(location_data_neighborhood):
            location_name, location_slug, location_type = location
            location_number = idx + 1
            location_schema = LocationCreateSchema(
                name=location_name,
                slug=f"{neighborhood_number}.{location_number}.{location_slug}",
                city_id=city_id,
                type=location_type,
                serial_number=location_number
            )
            locations_schemas.append(location_schema)

        return locations_schemas

        