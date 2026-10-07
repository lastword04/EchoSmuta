from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import ItemComponentCreateSchema, ItemComponentReadSchema
from ...services.items.items_component import ItemComponentServiceProtocol
from .production_catalog import PRODUCTION_ITEMS

# Словарь для сопоставления "простого" слага ресурса с его номером локации
# Этот словарь можно вынести в constants, если используется в других местах
RESOURCE_LOCATION_MAP = {
    # Болото (1)
    "plantain": 1,
    "motherwort": 1,
    "hypericum": 1,
    "coltsfoot": 1,
    "celandine": 1,
    "mint": 1,
    "thistle": 1,
    "yarrow": 1,
    "ginseng": 1,
    "tryn-trava": 1,
    # Шахта (2)
    "iron": 2,
    "sulfur": 2,
    "copper": 2,
    "silicon": 2,
    "mica": 2,
    "zinc": 2,
    "lead": 2,
    "tin": 2,
    # Прииск (3)
    "topaz": 3,
    "amethyst": 3,
    "opal": 3,
    "sapphire": 3,
    "emerald": 3,
    "ruby": 3,
    "diamond": 3,
    # Озеро (4)
    "goby": 4,
    "roach": 4,
    "crucian": 4,
    "carp": 4,
    "pike": 4,
    "catfish": 4,
    "sturgeon": 4,
    # Лес (5)
    "beech": 5,
    "oak": 5,
    "birch": 5,
    "spruce": 5,
    "mahogany": 5,
    # Пески (6)
    "meteor-dust": 6,
    "desert-nectar": 6,
    "dragon-feather": 6,
    "dragon-egg": 6,
    "enchanted-water": 6,
    "dragon-scale": 6,
    "sun-crystal": 6,
    # Шкуры (по локации выпадения)
    "skin-zverozhab": 1,
    "skin-lord-zverozhab": 1,
    "skin-gro": 2,
    "skin-big-gro": 2,
    "skin-zlatoglav": 3,
    "skin-zlatogriz": 3,
    "skin-shishiga": 4,
    "skin-morena": 4,
    "skin-kluvozyb": 5,
    "skin-kluvoklik": 5,
    "skin-skorpion": 6,
    "skin-red-skorpion": 6,
}

def get_full_resource_slug(resource_slug: str) -> str:
    """Возвращает полный слаг ресурса в формате i.r.{location}.3.{name}"""
    loc_num = RESOURCE_LOCATION_MAP.get(resource_slug)
    if loc_num is None:
        raise ValueError(f"Unknown resource slug: {resource_slug}")
    return f"i.r.{loc_num}.3.{resource_slug}"


class InitializeItemsComponentUseCaseProtocol(UseCaseProtocol[list[ItemComponentReadSchema]]):
    async def __call__(self: Self) -> list[ItemComponentReadSchema]:
        ...


class InitializeItemsComponentUseCase(InitializeItemsComponentUseCaseProtocol):
    def __init__(self: Self, service: ItemComponentServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[ItemComponentReadSchema]:
        used_items = await self.service.get_all()
        default_items = self._get_default_items()
        existing_pairs = {(item.item_slug, item.resource_slug) for item in used_items}
        items_to_create = [
            item for item in default_items
            if (item.item_slug, item.resource_slug) not in existing_pairs
        ]
        if items_to_create:
            await self.service.bulk_create(items_to_create)
        return await self.service.get_all()

    def _get_default_items(self: Self) -> list[ItemComponentCreateSchema]:
        items_data = [
            # Эликсиры для людей
            ("i.el.9.3.elixir-fierce-warrior", [("coltsfoot", 15), ("celandine", 15)]),
            ("i.el.9.3.elixir-pursuit", [("coltsfoot", 15), ("thistle", 15)]),
            ("i.el.9.3.moment-truth", [("enchanted-water", 10), ("yarrow", 15)]),
            ("i.el.9.3.white-day", [("plantain", 10)]),
            ("i.el.9.3.elixir-energy", [("coltsfoot", 8)]),
            
            # Эликсиры для орков
            ("i.el.9.3.elixir-unclean-force", [("dragon-scale", 8), ("ginseng", 12)]),
            ("i.el.9.3.elixir-bee-sting", [("thistle", 15), ("motherwort", 15)]),
            ("i.el.9.3.elixir-bear-song", [("mint", 15), ("motherwort", 15)]),
            ("i.el.9.3.elixir-soberness", [("plantain", 10)]),
            ("i.el.9.3.elixir-full-moon", [("motherwort", 8)]),
            
            # Эликсиры для эльфов
            ("i.el.9.3.elixir-cry-fools", [("hypericum", 15), ("celandine", 15)]),
            ("i.el.9.3.elixir-living-water", [("dragon-feather", 15), ("tryn-trava", 10)]),
            ("i.el.9.3.elixir-pink-light", [("mint", 15), ("hypericum", 15)]),
            ("i.el.9.3.elixir-light-way", [("plantain", 10)]),
            ("i.el.9.3.elixir-second-breath", [("hypericum", 8)]),
            
            # Внерасовые эликсиры
            ("i.el.9.3.elixir-dispersion", [("yarrow", 10), ("ginseng", 9), ("tryn-trava", 8), ("sun-crystal", 5)]),
            
            # Животные (питомник)
            ("i.an.24.1.giant-dragon", [("dragon-egg", 1), ("meteor-dust", 40), ("dragon-scale", 5), ("celandine", 5), ("goby", 15)]),
            ("i.an.24.1.mountain-dragon", [("dragon-egg", 1), ("desert-nectar", 40), ("sun-crystal", 5), ("mint", 5), ("roach", 15)]),
            ("i.an.24.1.ghost-dragon", [("dragon-egg", 1), ("desert-nectar", 50), ("dragon-feather", 40), ("thistle", 10), ("crucian", 5)]),
            ("i.an.24.1.river-dragon", [("dragon-egg", 1), ("dragon-feather", 50), ("enchanted-water", 45), ("yarrow", 15), ("carp", 10)]),
            ("i.an.24.1.battle-dragon", [("dragon-egg", 1), ("meteor-dust", 50), ("enchanted-water", 40), ("dragon-scale", 35), ("ginseng", 10), ("pike", 10)]),
            ("i.an.24.1.fire-dragon", [("dragon-egg", 1), ("meteor-dust", 60), ("desert-nectar", 60), ("dragon-feather", 40), ("sun-crystal", 25), ("dragon-scale", 10), ("tryn-trava", 10), ("catfish", 10)]),
            
            # Масла
            ("i.o.22.3.oil-against-swamp", [("skin-zverozhab", 15), ("dragon-egg", 10)]),
            ("i.o.22.3.oil-against-mine", [("skin-gro", 15), ("meteor-dust", 20)]),
            ("i.o.22.3.oil-against-lake", [("skin-shishiga", 15), ("enchanted-water", 5)]),
            ("i.o.22.3.oil-against-sands", [("skin-skorpion", 15), ("desert-nectar", 13)]),
            ("i.o.22.3.oil-against-quarry", [("skin-zlatoglav", 15), ("meteor-dust", 10), ("desert-nectar", 5)]),
            ("i.o.22.3.oil-against-forest", [("skin-kluvozyb", 15), ("dragon-feather", 8)]),
            ("i.o.22.3.treasure-oil", [("skin-lord-zverozhab", 5), ("skin-zlatogriz", 5), ("skin-big-gro", 5), ("dragon-scale", 5)]),
            ("i.o.22.3.tales-oil", [("skin-red-skorpion", 5), ("skin-kluvoklik", 5), ("skin-morena", 5), ("sun-crystal", 5)]),
            
            # Рыба
            ("i.f.25.3.dried-goby", [("goby", 8)]),
            ("i.f.25.3.dried-roach", [("roach", 8)]),
            ("i.f.25.3.dried-crucian", [("crucian", 7)]),
            ("i.f.25.3.fried-carp", [("carp", 7)]),
            ("i.f.25.3.fried-pike", [("pike", 6)]),
            ("i.f.25.3.fried-catfish", [("catfish", 6), ("yarrow", 1)]),
            ("i.f.25.3.smoked-sturgeon", [("sturgeon", 5), ("ginseng", 2), ("tryn-trava", 1)]),
            
            # Мебель
            ("i.fur.21.3.dining-table", [("beech", 20), ("oak", 10), ("copper", 5)]),
            ("i.fur.21.3.single-bed", [("beech", 10), ("birch", 20), ("zinc", 3)]),
            ("i.fur.21.3.armchair", [("oak", 10), ("birch", 5), ("mahogany", 2), ("skin-lord-zverozhab", 2)]),
            ("i.fur.21.3.chair", [("beech", 20), ("oak", 5)]),
            ("i.fur.21.3.small-bench", [("beech", 10), ("spruce", 5)]),
            ("i.fur.21.3.mirror", [("oak", 25), ("silicon", 10)]),
            ("i.fur.21.3.carpet", [("birch", 15), ("spruce", 7), ("mahogany", 2)]),
            ("i.fur.21.3.lamp", [("oak", 10), ("birch", 10)]),
        ]
        items_data.extend(
            (item.slug, list(item.components))
            for item in PRODUCTION_ITEMS
            if item.components
        )

        all_items = []

        for item in items_data:
            i_slug, components = item
            for resource_slug, resource_count in components:
                full_resource_slug = get_full_resource_slug(resource_slug)
                all_items.append(
                    ItemComponentCreateSchema(
                        item_slug=i_slug,
                        resource_slug=full_resource_slug,  # Используем правильный слаг
                        quantity=resource_count
                    )
                )
        return all_items
