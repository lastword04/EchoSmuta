"""Провайдеры purchase-домена: покупка предмета у магазина."""
from fastapi import Depends

from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisherProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..events.items import ItemEventsProtocol
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.sale.sale_history import SaleHistoryRepositoryProtocol
from ..repositories.sale.sale_inventory_items import SaleInventoryItemRepositoryProtocol
from ..repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.purchase.purchase_items import (
    PurchaseItemService,
    PurchaseItemServiceProtocol,
)
from ..use_cases.purchase.purchase_item import (
    PurchaseItemUseCase,
    PurchaseItemUseCaseProtocol,
)
from .adapters import get_character_service_client, get_item_template_service
from .events import get_items_events
from .repositories import (
    _get_character_item_repository,
    _get_city_trading_shop_character_repository,
    _get_city_trading_shop_settings_repository,
    _get_sale_inventory_item_repository,
    get_sale_history_repository,
)


# purchase items
def get_purchase_item_service(
    sale_repository: SaleInventoryItemRepositoryProtocol = Depends(_get_sale_inventory_item_repository),
    character_item_repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    shop_repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    city_settings_repository: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
    sale_history_repository: SaleHistoryRepositoryProtocol = Depends(get_sale_history_repository),
) -> PurchaseItemServiceProtocol:
    return PurchaseItemService(
        sale_repository=sale_repository,
        character_item_repository=character_item_repository,
        shop_repository=shop_repository,
        city_settings_repository=city_settings_repository,
        character_client=character_client,
        template_service=template_service,
        items_events=items_events,
        redis_publisher=redis_publisher,
        sale_history_repository=sale_history_repository,
    )

def get_purchase_item_use_case(
    service: PurchaseItemServiceProtocol = Depends(get_purchase_item_service)
) -> PurchaseItemUseCaseProtocol:
    return PurchaseItemUseCase(service=service)
