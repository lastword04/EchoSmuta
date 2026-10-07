import re
from decimal import Decimal
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....settings import settings
from ....core.clients.mining_client import MiningClient
from ....core.use_cases import UseCaseProtocol
from ..models import Resource, ResourceCategory, CurrentPrice, BuyoutStock


def _get_category(slug: str) -> ResourceCategory:
    if "skin" in slug:
        return ResourceCategory.SKINS
    match = re.search(r"i\.r\.(\d+)\.", slug)
    if match:
        num = int(match.group(1))
        mapping = {
            1: ResourceCategory.SWAMP,
            2: ResourceCategory.MINE,
            3: ResourceCategory.GEMS,
            4: ResourceCategory.LAKE,
            5: ResourceCategory.FOREST,
            6: ResourceCategory.SANDS,
        }
        return mapping.get(num, ResourceCategory.SWAMP)
    return ResourceCategory.SWAMP


class InitializeResourcesUseCaseProtocol(UseCaseProtocol[list[Resource]]):
    async def __call__(self: Self) -> list[Resource]:
        ...


class InitializeResourcesUseCase(InitializeResourcesUseCaseProtocol):
    # Карта цен покупки (скидка) – цена, по которой скупка покупает у игрока
    BUY_PRICE_MAP = {
        "plantain": 0.55,
        "motherwort": 1.17,
        "hypericum": 1.21,
        "coltsfoot": 1.23,
        "celandine": 2.04,
        "mint": 2.15,
        "thistle": 2.21,
        "yarrow": 2.71,
        "ginseng": 2.96,
        "tryn-trava": 3.53,
        "iron": 0.42,
        "sulfur": 1.13,
        "copper": 1.29,
        "silicon": 1.24,
        "mica": 2.29,
        "zinc": 2.31,
        "lead": 2.21,
        "tin": 4.24,
        "topaz": 1.02,
        "amethyst": 1.17,
        "opal": 1.35,
        "sapphire": 1.72,
        "emerald": 2.55,
        "ruby": 2.69,
        "diamond": 5.88,
        "goby": 0.39,
        "roach": 0.79,
        "crucian": 1.64,
        "carp": 1.98,
        "pike": 3.63,
        "catfish": 6.57,
        "sturgeon": 8.16,
        "beech": 0.57,
        "oak": 1.21,
        "birch": 1.32,
        "spruce": 3.32,
        "mahogany": 9.43,
        "meteor-dust": 0.76,
        "desert-nectar": 1.01,
        "dragon-feather": 1.28,
        "dragon-egg": 1.62,
        "enchanted-water": 2.12,
        "dragon-scale": 3.12,
        "sun-crystal": 3.22,
        "skin-zverozhab": 2.33,
        "skin-lord-zverozhab": 8.79,
        "skin-gro": 2.55,
        "skin-big-gro": 8.47,
        "skin-zlatoglav": 2.89,
        "skin-zlatogriz": 8.54,
        "skin-shishiga": 3.00,
        "skin-morena": 9.11,
        "skin-kluvozyb": 2.91,
        "skin-kluvoklik": 8.47,
        "skin-skorpion": 2.82,
        "skin-red-skorpion": 8.67,
    }

    # Карта цен продажи (наценка) – цена, по которой скупка продаёт игроку
    SELL_PRICE_MAP = {
        "plantain": 0.73,
        "motherwort": 1.48,
        "hypericum": 1.55,
        "coltsfoot": 1.52,
        "celandine": 2.45,
        "mint": 2.53,
        "thistle": 2.69,
        "yarrow": 3.05,
        "ginseng": 3.24,
        "tryn-trava": 4.02,
        "iron": 0.66,
        "sulfur": 1.65,
        "copper": 1.79,
        "silicon": 1.67,
        "mica": 2.67,
        "zinc": 2.81,
        "lead": 2.76,
        "tin": 7.2,
        "topaz": 1.21,
        "amethyst": 1.46,
        "opal": 1.78,
        "sapphire": 2.27,
        "emerald": 3.05,
        "ruby": 3.11,
        "diamond": 7.47,
        "goby": 0.84,
        "roach": 1.39,
        "crucian": 2.25,
        "carp": 2.53,
        "pike": 4.23,
        "catfish": 7.35,
        "sturgeon": 9.93,
        "beech": 0.82,
        "oak": 1.53,
        "birch": 1.61,
        "spruce": 5.76,
        "mahogany": 11.16,
        "meteor-dust": 1.13,
        "desert-nectar": 1.37,
        "dragon-feather": 1.64,
        "dragon-egg": 1.95,
        "enchanted-water": 2.38,
        "dragon-scale": 3.59,
        "sun-crystal": 3.67,
        "skin-zverozhab": 3.06,
        "skin-lord-zverozhab": 11.14,
        "skin-gro": 3.03,
        "skin-big-gro": 10.44,
        "skin-zlatoglav": 3.14,
        "skin-zlatogriz": 11.04,
        "skin-shishiga": 3.34,
        "skin-morena": 12.11,
        "skin-kluvozyb": 3.41,
        "skin-kluvoklik": 11.22,
        "skin-skorpion": 3.27,
        "skin-red-skorpion": 10.79,
    }

    def __init__(self, session: AsyncSession, mining_client: MiningClient):
        self.session = session
        self.mining_client = mining_client

    async def __call__(self) -> list[Resource]:
        # Проверяем, есть ли уже ресурсы
        existing = await self.session.scalars(select(Resource))
        existing_list = existing.all()
        if existing_list:
            return existing_list

        mining_resources = await self.mining_client.get_all_resources()

        for item in mining_resources:
            slug = item["slug"]
            # Извлекаем имя ресурса (последняя часть после точки)
            resource_name = slug.split('.')[-1]            
            buy_price = Decimal(str(self.BUY_PRICE_MAP.get(resource_name, 10.0000)))
            sell_price = Decimal(str(self.SELL_PRICE_MAP.get(resource_name, 10.0000)))

            # 1. Создаём ресурс (initial_price оставляем как sell_price, можно и buy_price)
            resource = Resource(
                external_resource_id=slug,
                code=slug,
                name=item["name"],
                icon_url=f"/images/resources/{slug}.png",
                source_type="RESOURCE_LOCATION",
                is_tradeable=True,
                base_sell_price=sell_price,
                base_buy_price=buy_price,
                min_sell_price=(sell_price * Decimal(str(settings.pricing.price_floor_multiplier))).quantize(Decimal("0.01")),
                max_sell_price=(sell_price * Decimal(str(settings.pricing.price_ceiling_multiplier))).quantize(Decimal("0.01")),
                min_buy_price=(buy_price * Decimal(str(settings.pricing.price_floor_multiplier))).quantize(Decimal("0.01")),
                max_buy_price=(buy_price * Decimal(str(settings.pricing.price_ceiling_multiplier))).quantize(Decimal("0.01")),                
                category=_get_category(slug),
                order=item.get("serial_number", 0),
            )
            self.session.add(resource)
            await self.session.flush()

            # 2. Создаём текущую цену (с двумя полями)
            current_price = CurrentPrice(
                resource_id=resource.id,
                sell_price=sell_price,
                buy_price=buy_price,
                previous_sell_price=None,
                previous_buy_price=None,
                last_recalculated_at=None,
                next_recalculation_at=None,
            )
            self.session.add(current_price)

            # 3. Создаём запас скупки (общий для всех)
            buyout_stock = BuyoutStock(
                resource_id=resource.id,
                quantity=10000,
            )
            self.session.add(buyout_stock)            
        
        await self.session.commit()
        result = await self.session.scalars(select(Resource))
        return list(result.all())