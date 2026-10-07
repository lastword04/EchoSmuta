"""Провайдеры sale-домена: продажа предметов + история продаж.

get_sale_history_repository живёт в .repositories, потому что им пользуется
ещё и purchase-домен.
"""
from fastapi import Depends

from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisherProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.sale.sale_history import SaleHistoryRepositoryProtocol
from ..repositories.sale.sale_inventory_items import SaleInventoryItemRepositoryProtocol
from ..services.character.character_items import CharacterItemServiceProtocol
from ..services.sale.sale_items import SaleItemService, SaleItemServiceProtocol
from ..use_cases.sale.add_item_to_sale import (
    AddItemToSaleUseCase,
    AddItemToSaleUseCaseProtocol,
)
from ..use_cases.sale.remove_item_from_sale import (
    RemoveItemFromSaleUseCase,
    RemoveItemFromSaleUseCaseProtocol,
)
from ..use_cases.sale.update_price import (
    UpdateSalePriceUseCase,
    UpdateSalePriceUseCaseProtocol,
)
from ..use_cases.sale_history.get_sales_history import (
    GetSalesHistoryUseCase,
)
from .adapters import get_character_service_client
from .character import get_character_item_service
from .repositories import (
    _get_character_item_repository,
    _get_city_trading_shop_character_repository,
    _get_sale_inventory_item_repository,
    get_sale_history_repository,
)


# sale items
def get_sale_item_service(
    sale_repository: SaleInventoryItemRepositoryProtocol = Depends(_get_sale_inventory_item_repository),
    character_item_repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    character_item_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
    shop_repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> SaleItemServiceProtocol:
    return SaleItemService(
        sale_repository=sale_repository,
        character_item_repository=character_item_repository,
        character_item_service=character_item_service,
        shop_repository=shop_repository,
        character_client=character_client,
        redis_publisher=redis_publisher,
    )

def get_add_item_to_sale_use_case(
    service: SaleItemServiceProtocol = Depends(get_sale_item_service)
) -> AddItemToSaleUseCaseProtocol:
    return AddItemToSaleUseCase(service=service)

def get_remove_item_from_sale_use_case(
    service: SaleItemServiceProtocol = Depends(get_sale_item_service)
) -> RemoveItemFromSaleUseCaseProtocol:
    return RemoveItemFromSaleUseCase(service=service)

def get_update_sale_price_use_case(
    service: SaleItemServiceProtocol = Depends(get_sale_item_service)
) -> UpdateSalePriceUseCaseProtocol:
    return UpdateSalePriceUseCase(service=service)


# История продаж
def get_get_sales_history_use_case(
    repository: SaleHistoryRepositoryProtocol = Depends(get_sale_history_repository),
) -> GetSalesHistoryUseCase:
    return GetSalesHistoryUseCase(repository)
