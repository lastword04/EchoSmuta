"""Провайдеры shop-домена: выставление/снятие предмета в магазине."""
from fastapi import Depends

from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisherProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.character.character_equipment import (
    CharacterEquipmentRepositoryProtocol,
)
from ..repositories.character.character_items import CharacterItemRepositoryProtocol
from ..repositories.city_trading_character.city_trading_shop import (
    CityTradingShopCharacterRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ..services.character.character_items import CharacterItemServiceProtocol
from ..services.shop.shop_items import ShopItemService, ShopItemServiceProtocol
from ..use_cases.shop.list_item_to_shop import (
    ListItemToShopUseCase,
    ListItemToShopUseCaseProtocol,
)
from ..use_cases.shop.withdraw_item_from_shop import (
    WithdrawItemFromShopUseCase,
    WithdrawItemFromShopUseCaseProtocol,
)
from .adapters import get_character_service_client
from .character import get_character_item_service
from .repositories import (
    _get_character_equipment_repository,
    _get_character_item_repository,
    _get_city_trading_shop_character_repository,
    _get_city_trading_shop_settings_repository,
)


# shop items
def get_shop_item_service(
    character_item_repository: CharacterItemRepositoryProtocol = Depends(_get_character_item_repository),
    shop_repository: CityTradingShopCharacterRepositoryProtocol = Depends(_get_city_trading_shop_character_repository),
    shop_settings_repository: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    character_item_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
    equipment_repository: CharacterEquipmentRepositoryProtocol = Depends(_get_character_equipment_repository),
    redis_publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> ShopItemServiceProtocol:
    return ShopItemService(
        character_item_repository=character_item_repository,
        shop_repository=shop_repository,
        shop_settings_repository=shop_settings_repository,
        character_client=character_client,
        character_item_service=character_item_service,
        equipment_repository=equipment_repository,
        redis_publisher=redis_publisher,
    )

def get_list_item_to_shop_use_case(
    service: ShopItemServiceProtocol = Depends(get_shop_item_service)
) -> ListItemToShopUseCaseProtocol:
    return ListItemToShopUseCase(service=service)

def get_withdraw_item_from_shop_use_case(
    service: ShopItemServiceProtocol = Depends(get_shop_item_service)
) -> WithdrawItemFromShopUseCaseProtocol:
    return WithdrawItemFromShopUseCase(service=service)
