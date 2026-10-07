from typing import Self

from shared.enums import Race

from .....core.use_cases import UseCaseProtocol
from ...enums import AnimalTransportType, ItemType
from ...schemas import ItemCreateSchema, ItemReadSchema
from ...services.items.items import ItemServiceProtocol
from .production_catalog import PRODUCTION_ITEMS


class InitializeItemsUseCaseProtocol(UseCaseProtocol[list[ItemReadSchema]]):
    async def __call__(self: Self) -> list[ItemReadSchema]:
        ...


class InitializeItemsUseCase(InitializeItemsUseCaseProtocol):
    def __init__(self: Self, service: ItemServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[ItemReadSchema]:
        used_items = await self.service.get_all()
        default_items = self._get_default_items()

        existing_slugs = {item.slug for item in used_items}

        items_to_create = [
            item for item in default_items
            if item.slug not in existing_slugs
        ]
        items_to_update = [
            item for item in default_items
            if item.slug in existing_slugs
        ]

        if items_to_create:
            await self.service.bulk_create(items_to_create)
        if items_to_update:
            await self.service.bulk_update(items_to_update)

        return await self.service.get_all()

    def _get_default_items(self: Self) -> list[ItemCreateSchema]:
        items_data = [
            # Название, slug, тип предмета
            # location_slug, цена, раса, индивидуальные параметры
            # параметры при использовании, этапы, опыт
            # минимальный срок годности, максимальный срок годности, минимальное количество, максимальное количество, уровень доступа, стакается ли
            ("Эликсир Свирепый Воин", "i.el.9.3.elixir-fierce-warrior", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.HUMAN, None, 
            {"power_number": 3}, 8, 4,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Преследование", "i.el.9.3.elixir-pursuit", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.HUMAN, None, 
            {"agility_number": 3}, 8, 4,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Момент Истины", "i.el.9.3.moment-truth", ItemType.ELIXIR, 
            "1.9.pharmacy", 3.0, 1, Race.HUMAN, None, 
            {"lucky_number": 5}, 10, 5,
            9, 10, 8, 14, 3, True, True),
            ("Эликсир Белый День", "i.el.9.3.white-day", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.3, 1, Race.HUMAN, None, 
            {"tiredness_percentage": -0.2}, 5, 2,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Энергия", "i.el.9.3.elixir-energy", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.8, 1, Race.HUMAN, None, 
            {"tiredness_percentage": -0.4}, 7, 3,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Сила Разума", "i.el.9.1.elixir-mind-strength", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.HUMAN, None, 
            {"power_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Скорость Звука", "i.el.9.1.elixir-speed-sound", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.HUMAN, None, 
            {"agility_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Улыбка Фортуны", "i.el.9.1.elixir-smile-fortune", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.HUMAN, None, 
            {"lucky_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Нечистая сила", "i.el.9.3.elixir-unclean-force", ItemType.ELIXIR, 
            "1.9.pharmacy", 3.0, 1, Race.ORC, None, 
            {"power_number": 5}, 8, 4,
            9, 10, 8, 14, 3, True, True),
            ("Эликсир Укус Пчелы", "i.el.9.3.elixir-bee-sting", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.ORC, None, 
            {"agility_number": 3}, 8, 4,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Медвежья песня", "i.el.9.3.elixir-bear-song", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.ORC, None, 
            {"lucky_number": 3}, 10, 5,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Трезвость", "i.el.9.3.elixir-soberness", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.3, 1, Race.ORC, None, 
            {"tiredness_percentage": -0.2}, 5, 2,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Полная Луна", "i.el.9.3.elixir-full-moon", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.8, 1, Race.ORC, None, 
            {"tiredness_percentage": -0.4}, 7, 3,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Сила Действия", "i.el.9.1.elixir-power-action", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ORC, None, 
            {"power_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Скорость Тигра", "i.el.9.1.elixir-tiger-speed", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ORC, None, 
            {"agility_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Шепот Фортуны", "i.el.9.3.elixir-whisper-fortune", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ORC, None, 
            {"lucky_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Плач Неразумных", "i.el.9.3.elixir-cry-fools", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.ELF, None, 
            {"power_number": 3}, 8, 4,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Живая Вода", "i.el.9.3.elixir-living-water", ItemType.ELIXIR, 
            "1.9.pharmacy", 3.0, 1, Race.ELF, None, 
            {"agility_number": 5}, 8, 4,
            9, 10, 8, 14, 3, True, True),
            ("Эликсир Розовый Свет", "i.el.9.3.elixir-pink-light", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.5, 1, Race.ELF, None, 
            {"lucky_number": 3}, 10, 5,
            9, 10, 12, 18, 3, True, True),
            ("Эликсир Легкий Путь", "i.el.9.3.elixir-light-way", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.3, 1, Race.ELF, None, 
            {"tiredness_percentage": -0.2}, 5, 2,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Второе Дыхание", "i.el.9.3.elixir-second-breath", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.8, 1, Race.ELF, None, 
            {"tiredness_percentage": -0.4}, 7, 3,
            7, 8, 20, 30, 3, True, True),
            ("Эликсир Сила Духа", "i.el.9.1.elixir-spirit-strength", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ELF, None, 
            {"power_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Скорость Ястреба", "i.el.9.1.elixir-hawk-speed", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ELF, None, 
            {"agility_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Танец Фортуны", "i.el.9.1.elixir-dance-fortune", ItemType.ELIXIR, 
            "1.9.pharmacy", 0.1, 1, Race.ELF, None, 
            {"lucky_number": 1}, None, None,
            7, 8, 20, 30, 1, True, True),
            ("Эликсир Развеивания", "i.el.9.3.elixir-dispersion", ItemType.ELIXIR, 
            "1.9.pharmacy", 10.0, 2, None, None, 
            {"dispel_all_effects": True}, 12, 6,
            13, 14, 5, 9, 3, True, True),
            ("Эликсир Вечной Жизни", "i.el.9.3.elixir-eternal-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 6.0, 10, None, None, 
            {"health_number": 360}, None, None,
            30, 30, 1, 1, 3, True, False),
            ("Эликсир Грааль Жизни", "i.el.9.3.elixir-grail-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 5.0, 9, None, None, 
            {"health_number": 240}, None, None,
            17, 18, 1, 1, 3, True, True),
            ("Эликсир Кубок Жизни", "i.el.9.3.elixir-cup-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 4.0, 8, None, None, 
            {"health_number": 180}, None, None,
            14, 16, 1, 1, 3, True, True),
            ("Эликсир Чаша Жизни", "i.el.9.3.elixir-chalice-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 3.0, 6, None, None, 
            {"health_number": 120}, None, None,
            12, 14, 1, 1, 3, True, True),
            ("Эликсир Глоток Жизни", "i.el.9.1.elixir-sip-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.0, 4, None, None, 
            {"health_number": 60}, None, None,
            9, 10, 1, 1, 1, True, True),
            ("Эликсир Капля Жизни", "i.el.9.1.elixir-drop-life", ItemType.ELIXIR, 
            "1.9.pharmacy", 1.0, 2, None, None, 
            {"health_number": 30}, None, None,
            7, 8, 1, 1, 1, True, True),
            ("Эликсир Небесный Поток", "i.el.9.3.elixir-heavenly-stream", ItemType.ELIXIR, 
            "1.9.pharmacy", 3.0, 6, None, None, 
            {"mana_number": 90}, None, None,
            12, 14, 1, 1, 3, True, True),
            ("Эликсир Лагуна Мудрости", "i.el.9.3.elixir-lagoon-wisdom", ItemType.ELIXIR, 
            "1.9.pharmacy", 2.0, 4, None, None, 
            {"mana_number": 60}, None, None,
            9, 10, 1, 1, 3, True, True),
            ("Эликсир Волшебная Слеза", "i.el.9.3.elixir-magic-tear", ItemType.ELIXIR, 
            "1.9.pharmacy", 1.0, 2, None, None, 
            {"mana_number": 30}, None, None,
            7, 8, 1, 1, 3, True, True),

            # Animals
            ("Великанский дракон", "i.an.24.1.giant-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 5.0, 1, None, {"speed": 2, "transport_type": AnimalTransportType.LAND.value}, 
            {"increase_carry_weight": 120}, 12, 5,
            90, 90, 1, 1, 1, False, True),
            ("Горный дракон", "i.an.24.1.mountain-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 10.0, 1, None, {"speed": 3, "transport_type": AnimalTransportType.LAND.value}, 
            {"attributes_number": 1}, 14, 6,
            90, 90, 1, 1, 1, False, True),
            ("Призрачный дракон", "i.an.24.1.ghost-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 20.0, 1, None, {"speed": 5, "transport_type": AnimalTransportType.AIR.value}, 
            {"invisible_way": True}, 18, 7,
            60, 60, 1, 1, 1, False, True),
            ("Речной дракон", "i.an.24.1.river-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 30.0, 1, None, {"speed": 7, "transport_type": AnimalTransportType.AIR.value}, 
            {"max_health_percentage": 0.2}, 20, 8,
            30, 30, 1, 1, 1, False, True),
            ("Боевой дракон", "i.an.24.1.battle-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 50.0, 1, None, {"speed": 7, "transport_type": AnimalTransportType.AIR.value}, 
            {"summon_additional_beast": True}, 22, 9,
            30, 30, 1, 1, 1, False, True),
            ("Огненный дракон", "i.an.24.1.fire-dragon", ItemType.ANIMAL, 
            "1.24.bird-market", 60.0, 1, None, {"speed": 10, "transport_type": AnimalTransportType.AIR.value}, 
            {"accelerated_recovery": True}, 25, 10,
            60, 60, 1, 1, 1, False, True),

            # Oils
            ("Масло против Зверожабов", "i.o.22.3.oil-against-swamp", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_swamp_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло против Гро", "i.o.22.3.oil-against-mine", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_mine_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло против Шишиг", "i.o.22.3.oil-against-lake", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_lake_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло против Скорпионов", "i.o.22.3.oil-against-sands", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_sands_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло против Златоглавов", "i.o.22.3.oil-against-quarry", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_quarry_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло против Клювозубов", "i.o.22.3.oil-against-forest", ItemType.OIL, 
            "1.22.hunting-shop", 2.0, 1, None, {"max_used": 30}, 
            {"attack_against_forest_percentage": 0.15}, 8, 3,
            10, 11, 15, 15, 3, True, True),
            ("Масло Сокровений", "i.o.22.3.treasure-oil", ItemType.OIL, 
            "1.22.hunting-shop", 5.0, 1, None, {"max_used": 60}, 
            {"attack_against_labyrinth_percentage": 0.15}, 10, 5,
            12, 13, 15, 15, 3, True, True),
            ("Масло Сказаний", "i.o.22.3.tales-oil", ItemType.OIL, 
            "1.22.hunting-shop", 5.0, 1, None, {"max_used": 60}, 
            {"attack_against_library_percentage": 0.15}, 10, 5,
            12, 13, 15, 15, 3, True, True),

            # Fish
            ("Вяленый Ерш", "i.f.25.3.dried-goby", ItemType.FISH, 
            "1.25.fish-shop", 0.5, 1, None, None, 
            {"tiredness_percentage": -0.15}, 5, 1,
            17, 18, 15, 25, 3, True, True),
            ("Вяленая Плотва", "i.f.25.3.dried-roach", ItemType.FISH, 
            "1.25.fish-shop", 0.5, 1, None, None, 
            {"tiredness_percentage": -0.3}, 6, 2,
            17, 18, 15, 25, 3, True, True),
            ("Вяленый Карась", "i.f.25.3.dried-crucian", ItemType.FISH, 
            "1.25.fish-shop", 0.5, 1, None, None, 
            {"tiredness_percentage": -0.5}, 7, 3,
            17, 18, 15, 25, 3, True, True),
            ("Жареный Карп", "i.f.25.3.fried-carp", ItemType.FISH, 
            "1.25.fish-shop", 1.0, 2, None, None, 
            {"health_number": 175}, 7, 3,
            14, 15, 14, 20, 3, True, True),
            ("Жареная Щука", "i.f.25.3.fried-pike", ItemType.FISH, 
            "1.25.fish-shop", 1.5, 2, None, None, 
            {"health_number": 250}, 8, 4,
            14, 15, 14, 20, 3, True, True),
            ("Жареный Сом", "i.f.25.3.fried-catfish", ItemType.FISH, 
            "1.25.fish-shop", 2.0, 2, None, None, 
            {"health_number": 350}, 9, 5,
            14, 15, 14, 20, 3, True, True),
            ("Копченый Осетр", "i.f.25.3.smoked-sturgeon", ItemType.FISH, 
            "1.25.fish-shop", 4.0, 3, None, None, 
            {"health_number": 500, "tiredness_percentage": -0.5}, 10, 7,
            14, 15, 8, 16, 3, True, True),

            # Furniture
            ("Стол обеденный", "i.fur.21.3.dining-table", ItemType.FURNITURE, 
            "1.21.furniture-shop", 50.0, 30, None, {"volume": 40, "max_wear": 200}, 
            {"health_percentage": 0.75, "health_percentage_weared": 0.0}, 8, 5,
            None, None, 1, 1, 1, False, True),
            ("Кровать одноместная", "i.fur.21.3.single-bed", ItemType.FURNITURE, 
            "1.21.furniture-shop", 50.0, 20, None, {"volume": 30, "max_wear": 200}, 
            {"tiredness_percentage": 2.0, "tiredness_percentage_weared": 0.25}, 10, 5,
            None, None, 1, 1, 1, False, True),
            ("Кресло", "i.fur.21.3.armchair", ItemType.FURNITURE, 
            "1.21.furniture-shop", 37.0, 20, None, {"volume": 20, "max_wear": 150}, 
            {"health_percentage": 0.5, "health_percentage_weared": 0.15, "tiredness_percentage": 2.0, "tiredness_percentage_weared": 0.25}, 10, 5,
            None, None, 1, 1, 1, False, True),
            ("Стул", "i.fur.21.3.chair", ItemType.FURNITURE, 
            "1.21.furniture-shop", 15.0, 10, None, {"volume": 10, "max_wear": 50}, 
            {"health_percentage": 0.25, "health_percentage_weared": 0.25}, 5, 2,
            None, None, 1, 1, 1, False, True),
            ("Лавка малая", "i.fur.21.3.small-bench", ItemType.FURNITURE, 
            "1.21.furniture-shop", 15.0, 10, None, {"volume": 20, "max_wear": 50}, 
            {"tiredness_percentage": 0.5, "tiredness_percentage_weared": 0.5}, 5, 2,
            None, None, 1, 1, 1, False, True),
            ("Зеркало", "i.fur.21.3.mirror", ItemType.FURNITURE, 
            "1.21.furniture-shop", 25.0, 10, None, {"volume": 10, "max_wear": 150}, 
            {"mana_percentage": 2.0, "mana_percentage_weared": 0.0}, 8, 5,
            None, None, 1, 1, 1, False, True),
            ("Ковер", "i.fur.21.3.carpet", ItemType.FURNITURE, 
            "1.21.furniture-shop", 30.0, 5, None, {"volume": 20, "max_wear": 200}, 
            {"mana_percentage": 1.0, "mana_percentage_weared": 0.1, "health_percentage": 0.25, "health_percentage_weared": 0.1, 
            "tiredness_percentage": 0.25, "tiredness_percentage_weared": 0.25}, 10, 5,
            None, None, 1, 1, 1, False, True),
            ("Светильник", "i.fur.21.3.lamp", ItemType.FURNITURE, 
            "1.21.furniture-shop", 10.0, 5, None, {"volume": 10, "max_wear": 50}, 
            {"mana_percentage": 0.5, "mana_percentage_weared": 0.25}, 5, 2,
            None, None, 1, 1, 1, False, True),
        ]

        all_items = [
            ItemCreateSchema(
                name=item.name,
                slug=item.slug,
                item_type=item.item_type,
                location_slug=item.location_slug,
                price=item.price,
                weight=item.weight,
                race=item.race,
                parameters=item.parameters,
                ability_parameters=item.ability_parameters,
                craft_stages=item.craft_stages,
                craft_experience=item.craft_experience,
                minimal_level=item.minimal_level,
                is_stackable=False,
                can_sell=True,
            )
            for item in PRODUCTION_ITEMS
        ]

        for item in items_data:
            i_name, i_slug, i_type, i_location, i_price, \
            i_weight, i_race, i_parameters, i_ability_parameters, \
            i_craft_stages, i_craft_expierence, i_min_life_d, \
            i_max_life_d, i_min_quantity, i_max_quantity, \
            i_min_level, i_is_stackable, i_can_sell = item
           
            all_items.append(
                ItemCreateSchema(
                    name=i_name,
                    slug=i_slug,
                    item_type=i_type,
                    location_slug=i_location,
                    price=i_price,
                    weight=i_weight,
                    race=i_race,
                    parameters=i_parameters,
                    ability_parameters=i_ability_parameters,
                    craft_stages=i_craft_stages,
                    craft_experience=i_craft_expierence,
                    min_shelf_life_days=i_min_life_d,
                    max_shelf_life_days=i_max_life_d,
                    min_output_quantity=i_min_quantity,
                    max_output_quantity=i_max_quantity,
                    minimal_level=i_min_level,
                    is_stackable=i_is_stackable,
                    can_sell=i_can_sell
                )
            )
        return all_items
