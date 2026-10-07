from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationResourceCreateSchema, LocationResourceReadSchema
from ...services.location_resources import LocationResourceServiceProtocol


class InitializeLocationResourcesUseCaseProtocol(UseCaseProtocol[list[LocationResourceReadSchema]]):
    async def __call__(self: Self) -> list[LocationResourceReadSchema]:
        ...


class InitializeLocationResourcesUseCase(InitializeLocationResourcesUseCaseProtocol):
    def __init__(self: Self, service: LocationResourceServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[LocationResourceReadSchema]:
        used_location_resources = await self.service.get_all()
        default_resources = self._get_default_location_resources(2)
        if len(used_location_resources) == len(default_resources):
            return used_location_resources
        if len(used_location_resources) != 0:
            raise ValueError("Resources not corrected count.")

        return await self.service.bulk_create(default_resources)

    def _get_default_location_resources(self: Self, city_number: int) -> list[LocationResourceCreateSchema]:
        # Сопоставление: (Название ресурса, Slug, Уровень (опыт), Шанс (в долях), Доступно (max_amount))
        
        resource_data_with_details = [
            # БОЛОТО (Собирать)
            ("Подорожник", "plantain", 1, 0.28, 14000),
            ("Пустырник", "motherwort", 2, 0.15, 7500),
            ("Зверобой", "hypericum", 2, 0.15, 7500),
            ("Мать-и-мачеха", "coltsfoot", 2, 0.15, 7500),
            ("Чистотел", "celandine", 3, 0.08, 4000),
            ("Мята", "mint", 3, 0.07, 3500),
            ("Чертополох", "thistle", 3, 0.06, 3000),
            ("Тысячелистник", "yarrow", 4, 0.03, 1500),
            ("Женьшень", "ginseng", 4, 0.02, 1000),
            ("Трын-трава", "tryn-trava", 5, 0.01, 500),

            # ОЗЕРО (Забросить - Рыба)
            ("Ёрш", "goby", 1, 0.32, 16000),
            ("Плотва", "roach", 1, 0.32, 16000),
            ("Карась", "crucian", 3, 0.18, 9000),
            ("Карп", "carp", 4, 0.10, 5000),
            ("Щука", "pike", 5, 0.05, 2500),
            ("Сом", "catfish", 6, 0.02, 1000),
            ("Осётр", "sturgeon", 6, 0.01, 500),

            # ЛЕС (Рубить - Деревья)
            ("Бук", "beech", 1, 0.40, 20000),
            ("Дуб", "oak", 2, 0.25, 12500),
            ("Берёза", "birch", 2, 0.25, 12500),
            ("Ель", "spruce", 5, 0.08, 4000),
            ("Красное дерево", "mahogany", 6, 0.02, 1000),

            # ШАХТА (Копать - Руда)
            ("Железо", "iron", 1, 0.31, 15500),
            ("Сера", "sulfur", 2, 0.14, 7000),
            ("Медь", "copper", 2, 0.14, 7000),
            ("Кремний", "silicon", 2, 0.14, 7000),
            ("Слюда", "mica", 3, 0.08, 4000),
            ("Цинк", "zinc", 3, 0.08, 4000),
            ("Свинец", "lead", 3, 0.08, 4000),
            ("Олово", "tin", 4, 0.03, 1500),

            # ПРИИСК (Добывать - Самоцветы)
            ("Топаз", "topaz", 1, 0.25, 12500),
            ("Аметист", "amethyst", 1, 0.22, 11000),
            ("Опал", "opal", 2, 0.20, 10000),
            ("Сапфир", "sapphire", 3, 0.15, 7500),
            ("Изумруд", "emerald", 4, 0.08, 4000),
            ("Рубин", "ruby", 4, 0.08, 4000),
            ("Алмаз", "diamond", 5, 0.02, 1000),

            # ПЕСКИ (Исследовать - Находки)
            ("Метеоритная пыль", "meteor-dust", 1, 0.30, 15000),
            ("Пустынный нектар", "desert-nectar", 1, 0.22, 11000),
            ("Перо дракона", "dragon-feather", 2, 0.17, 8500),
            ("Яйцо дракона", "dragon-egg", 3, 0.13, 6500),
            ("Зачарованная вода", "enchanted-water", 4, 0.08, 4000),
            ("Чешуя дракона", "dragon-scale", 5, 0.05, 2500),
            ("Солнечный кристалл", "sun-crystal", 5, 0.05, 2500),
        ]

        # Сопоставление ресурса с его локацией
        # Первая цифра - номер города, вторая цифра - номер локации
        # Номера локаций по умолчанию:
        # Болото 1
        # Шахта 2
        # Прииск 3
        # Озеро 4
        # Лес 5
        # Пески 6
        # Значение ключа - это кортеж, где первое значение - номер города, второе - номер локации, третье - остаточный slug локации
        resource_to_location = {
            # Болото
            "plantain": (city_number, 1, "swamp"),
            "motherwort": (city_number, 1, "swamp"),
            "hypericum": (city_number, 1, "swamp"),
            "coltsfoot": (city_number, 1, "swamp"),
            "celandine": (city_number, 1, "swamp"),
            "mint": (city_number, 1, "swamp"),
            "thistle": (city_number, 1, "swamp"),
            "yarrow": (city_number, 1, "swamp"),
            "ginseng": (city_number, 1, "swamp"),
            "tryn-trava": (city_number, 1, "swamp"),
            # Шахта
            "iron": (city_number, 2, "shaft"),
            "sulfur": (city_number, 2, "shaft"),
            "copper": (city_number, 2, "shaft"),
            "silicon": (city_number, 2, "shaft"),
            "mica": (city_number, 2, "shaft"),
            "zinc": (city_number, 2, "shaft"),
            "lead": (city_number, 2, "shaft"),
            "tin": (city_number, 2, "shaft"),
            # Прииск
            "topaz": (city_number, 3, "mine"),
            "amethyst": (city_number, 3, "mine"),
            "opal": (city_number, 3, "mine"),
            "sapphire": (city_number, 3, "mine"),
            "emerald": (city_number, 3, "mine"),
            "ruby": (city_number, 3, "mine"),
            "diamond": (city_number, 3, "mine"),
            # Озеро
            "goby": (city_number, 4, "lake"),
            "roach": (city_number, 4, "lake"),
            "crucian": (city_number, 4, "lake"),
            "carp": (city_number, 4, "lake"),
            "pike": (city_number, 4, "lake"),
            "catfish": (city_number, 4, "lake"),
            "sturgeon": (city_number, 4, "lake"),
            # Лес
            "beech": (city_number, 5, "forest"),
            "oak": (city_number, 5, "forest"),
            "birch": (city_number, 5, "forest"),
            "spruce": (city_number, 5, "forest"),
            "mahogany": (city_number, 5, "forest"),
            # Пески
            "meteor-dust": (city_number, 6, "sands"),
            "desert-nectar": (city_number, 6, "sands"),
            "dragon-feather": (city_number, 6, "sands"),
            "dragon-egg": (city_number, 6, "sands"),
            "enchanted-water": (city_number, 6, "sands"),
            "dragon-scale": (city_number, 6, "sands"),
            "sun-crystal": (city_number, 6, "sands"),
        }

        locations_resources_schemas = []
        for _, r_slug, r_experience, r_chance, r_available in resource_data_with_details:
            city_number, location_number, location_slug = resource_to_location[r_slug]
            locations_resources_schema = LocationResourceCreateSchema(
                location_slug=f"{city_number}.{location_number}.{location_slug}",
                resource_slug=f"i.r.{location_number}.3.{r_slug}",
                chance=r_chance,
                experience_on_resource=r_experience,
                current_amount=r_available,
                max_amount=r_available,
            )

            locations_resources_schemas.append(locations_resources_schema)

        return locations_resources_schemas