from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import ItemPriceCreateSchema, ItemPriceReadSchema
from ...services.items.items_price import ItemPriceServiceProtocol
from .production_catalog import PRODUCTION_ITEMS


class InitializeItemsPriceUseCaseProtocol(UseCaseProtocol[list[ItemPriceReadSchema]]):
    async def __call__(self: Self) -> list[ItemPriceReadSchema]:
        ...


class InitializeItemsPriceUseCase(InitializeItemsPriceUseCaseProtocol):
    def __init__(self: Self, service: ItemPriceServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[ItemPriceReadSchema]:
        used_items = await self.service.get_all()
        default_items = self._get_default_items()
        existing_pairs = {(item.item_slug, item.quantity) for item in used_items}
        items_to_create = [
            item for item in default_items
            if (item.item_slug, item.quantity) not in existing_pairs
        ]
        if items_to_create:
            await self.service.bulk_create(items_to_create)
        return await self.service.get_all()

    def _get_default_items(self: Self) -> list[ItemPriceCreateSchema]:
        # Старые предметы (эликсиры, масла, рыба, мебель, драконы) — без изменений
        items_data = [
            # Эликсиры для людей
            ("i.el.9.3.elixir-fierce-warrior", 35.0, 20),
            ("i.el.9.3.elixir-fierce-warrior", 75.0, 50),
            ("i.el.9.3.elixir-fierce-warrior", 140.0, 100),
            ("i.el.9.3.elixir-pursuit", 35.0, 20),
            ("i.el.9.3.elixir-pursuit", 75.0, 50),
            ("i.el.9.3.elixir-pursuit", 140.0, 100),
            ("i.el.9.3.moment-truth", 40.0, 20),
            ("i.el.9.3.moment-truth", 85.0, 50),
            ("i.el.9.3.moment-truth", 155.0, 100),
            ("i.el.9.3.white-day", 30.0, 20),
            ("i.el.9.3.white-day", 65.0, 50),
            ("i.el.9.3.white-day", 120.0, 100),
            ("i.el.9.3.elixir-energy", 30.0, 20),
            ("i.el.9.3.elixir-energy", 65.0, 50),
            ("i.el.9.3.elixir-energy", 120.0, 100),
            
            # Эликсиры для орков
            ("i.el.9.3.elixir-unclean-force", 40.0, 20),
            ("i.el.9.3.elixir-unclean-force", 85.0, 50),
            ("i.el.9.3.elixir-unclean-force", 155.0, 100),
            ("i.el.9.3.elixir-bee-sting", 35.0, 20),
            ("i.el.9.3.elixir-bee-sting", 75.0, 50),
            ("i.el.9.3.elixir-bee-sting", 140.0, 100),
            ("i.el.9.3.elixir-bear-song", 35.0, 20),
            ("i.el.9.3.elixir-bear-song", 75.0, 50),
            ("i.el.9.3.elixir-bear-song", 140.0, 100),
            ("i.el.9.3.elixir-soberness", 30.0, 20),
            ("i.el.9.3.elixir-soberness", 65.0, 50),
            ("i.el.9.3.elixir-soberness", 120.0, 100),
            ("i.el.9.3.elixir-full-moon", 30.0, 20),
            ("i.el.9.3.elixir-full-moon", 65.0, 50),
            ("i.el.9.3.elixir-full-moon", 120.0, 100),
            
            # Эликсиры для эльфов
            ("i.el.9.3.elixir-cry-fools", 35.0, 20),
            ("i.el.9.3.elixir-cry-fools", 75.0, 50),
            ("i.el.9.3.elixir-cry-fools", 140.0, 100),
            ("i.el.9.3.elixir-living-water", 40.0, 20),
            ("i.el.9.3.elixir-living-water", 85.0, 50),
            ("i.el.9.3.elixir-living-water", 155.0, 100),
            ("i.el.9.3.elixir-pink-light", 35.0, 20),
            ("i.el.9.3.elixir-pink-light", 75.0, 50),
            ("i.el.9.3.elixir-pink-light", 140.0, 100),
            ("i.el.9.3.elixir-light-way", 30.0, 20),
            ("i.el.9.3.elixir-light-way", 65.0, 50),
            ("i.el.9.3.elixir-light-way", 120.0, 100),
            ("i.el.9.3.elixir-second-breath", 30.0, 20),
            ("i.el.9.3.elixir-second-breath", 65.0, 50),
            ("i.el.9.3.elixir-second-breath", 120.0, 100),
            
            # Внерасовые эликсиры
            ("i.el.9.3.elixir-dispersion", 50.0, 20),
            ("i.el.9.3.elixir-dispersion", 105.0, 50),
            ("i.el.9.3.elixir-dispersion", 190.0, 100),
            
            # Животные (питомник)
            ("i.an.24.1.giant-dragon", 10.0, 1),
            ("i.an.24.1.giant-dragon", 45.0, 5),
            ("i.an.24.1.giant-dragon", 80.0, 10),
            ("i.an.24.1.mountain-dragon", 15.0, 1),
            ("i.an.24.1.mountain-dragon", 65.0, 5),
            ("i.an.24.1.mountain-dragon", 125.0, 10),
            ("i.an.24.1.ghost-dragon", 35.0, 1),
            ("i.an.24.1.ghost-dragon", 170.0, 5),
            ("i.an.24.1.ghost-dragon", 330.0, 10),
            ("i.an.24.1.river-dragon", 40.0, 1),
            ("i.an.24.1.river-dragon", 190.0, 5),
            ("i.an.24.1.river-dragon", 370.0, 10),
            ("i.an.24.1.battle-dragon", 75.0, 1),
            ("i.an.24.1.battle-dragon", 365.0, 5),
            ("i.an.24.1.battle-dragon", 715.0, 10),
            ("i.an.24.1.fire-dragon", 80.0, 1),
            ("i.an.24.1.fire-dragon", 390.0, 5),
            ("i.an.24.1.fire-dragon", 765.0, 10),
            
            # Масла
            ("i.o.22.3.oil-against-swamp", 30.0, 20),
            ("i.o.22.3.oil-against-swamp", 65.0, 50),
            ("i.o.22.3.oil-against-swamp", 120.0, 100),
            ("i.o.22.3.oil-against-mine", 30.0, 20),
            ("i.o.22.3.oil-against-mine", 65.0, 50),
            ("i.o.22.3.oil-against-mine", 120.0, 100),
            ("i.o.22.3.oil-against-lake", 30.0, 20),
            ("i.o.22.3.oil-against-lake", 65.0, 50),
            ("i.o.22.3.oil-against-lake", 120.0, 100),
            ("i.o.22.3.oil-against-sands", 30.0, 20),
            ("i.o.22.3.oil-against-sands", 65.0, 50),
            ("i.o.22.3.oil-against-sands", 120.0, 100),
            ("i.o.22.3.oil-against-quarry", 30.0, 20),
            ("i.o.22.3.oil-against-quarry", 65.0, 50),
            ("i.o.22.3.oil-against-quarry", 120.0, 100),
            ("i.o.22.3.oil-against-forest", 30.0, 20),
            ("i.o.22.3.oil-against-forest", 65.0, 50),
            ("i.o.22.3.oil-against-forest", 120.0, 100),
            ("i.o.22.3.treasure-oil", 40.0, 20),
            ("i.o.22.3.treasure-oil", 85.0, 50),
            ("i.o.22.3.treasure-oil", 155.0, 100),
            ("i.o.22.3.tales-oil", 40.0, 20),
            ("i.o.22.3.tales-oil", 85.0, 50),
            ("i.o.22.3.tales-oil", 155.0, 100),
            
            # Рыба
            ("i.f.25.3.dried-goby", 7.0, 20),
            ("i.f.25.3.dried-goby", 15.0, 50),
            ("i.f.25.3.dried-goby", 30.0, 100),
            ("i.f.25.3.dried-roach", 15.0, 20),
            ("i.f.25.3.dried-roach", 30.0, 50),
            ("i.f.25.3.dried-roach", 50.0, 100),
            ("i.f.25.3.dried-crucian", 20.0, 20),
            ("i.f.25.3.dried-crucian", 40.0, 50),
            ("i.f.25.3.dried-crucian", 70.0, 100),
            ("i.f.25.3.fried-carp", 20.0, 20),
            ("i.f.25.3.fried-carp", 40.0, 50),
            ("i.f.25.3.fried-carp", 70.0, 100),
            ("i.f.25.3.fried-pike", 25.0, 20),
            ("i.f.25.3.fried-pike", 55.0, 50),
            ("i.f.25.3.fried-pike", 100.0, 100),
            ("i.f.25.3.fried-catfish", 30.0, 20),
            ("i.f.25.3.fried-catfish", 65.0, 50),
            ("i.f.25.3.fried-catfish", 120.0, 100),
            ("i.f.25.3.smoked-sturgeon", 40.0, 20),
            ("i.f.25.3.smoked-sturgeon", 80.0, 50),
            ("i.f.25.3.smoked-sturgeon", 150.0, 100),
            
            # Мебель
            ("i.fur.21.3.dining-table", 20.0, 20),
            ("i.fur.21.3.dining-table", 45.0, 50),
            ("i.fur.21.3.dining-table", 80.0, 100),
            ("i.fur.21.3.single-bed", 30.0, 20),
            ("i.fur.21.3.single-bed", 65.0, 50),
            ("i.fur.21.3.single-bed", 120.0, 100),
            ("i.fur.21.3.armchair", 50.0, 20),
            ("i.fur.21.3.armchair", 110.0, 50),
            ("i.fur.21.3.armchair", 200.0, 100),
            ("i.fur.21.3.chair", 25.0, 20),
            ("i.fur.21.3.chair", 55.0, 50),
            ("i.fur.21.3.chair", 100.0, 100),
            ("i.fur.21.3.small-bench", 35.0, 20),
            ("i.fur.21.3.small-bench", 75.0, 50),
            ("i.fur.21.3.small-bench", 140.0, 100),
            ("i.fur.21.3.mirror", 25.0, 20),
            ("i.fur.21.3.mirror", 55.0, 50),
            ("i.fur.21.3.mirror", 100.0, 100),
            ("i.fur.21.3.carpet", 40.0, 20),
            ("i.fur.21.3.carpet", 85.0, 50),
            ("i.fur.21.3.carpet", 150.0, 100),
            ("i.fur.21.3.lamp", 35.0, 20),
            ("i.fur.21.3.lamp", 75.0, 50),
            ("i.fur.21.3.lamp", 140.0, 100),
        ]

        # Новые предметы (Кузница и Ювелирная)
        for item in PRODUCTION_ITEMS:
            if item.craft_stages is not None and item.components:
                # Базовая цена за 1 рецепт
                base_price = item.minimal_level * 10 + (item.craft_experience or 0) * 5
                # Добавляем три записи: 1, 5, 10
                items_data.append((item.slug, base_price, 1))
                items_data.append((item.slug, base_price * 4, 5))
                items_data.append((item.slug, base_price * 7, 10))

        all_items = []
        for i_slug, i_price, i_quantity in items_data:
            all_items.append(
                ItemPriceCreateSchema(
                    item_slug=i_slug,
                    price=i_price,
                    quantity=i_quantity,
                )
            )
        return all_items