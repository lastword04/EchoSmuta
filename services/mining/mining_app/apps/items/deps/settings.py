"""Провайдеры настроек городского торгового магазина (settings-домен).

Репозитории настроек шарится между character/shop/purchase/settings,
поэтому сами провайдеры лежат в deps/repositories.py, а сервисы и
use-case чтения — здесь (use_cases/settings/).
"""
from fastapi import Depends

from ..adapters.characters import CharacterServiceClientProtocol
from ..repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_settings import (
    CityTradingShopSettingsRepositoryProtocol,
)
from ..services.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsForCharacterService,
    CityTradingShopBuySettingsForCharacterServiceProtocol,
    CityTradingShopBuySettingsService,
    CityTradingShopBuySettingsServiceProtocol,
)
from ..services.settings.city_trading_shop_settings import (
    CityTradingShopSettingsService,
    CityTradingShopSettingsServiceProtocol,
)
from ..use_cases.settings.get_settings_trading_shop_buy_by_loc_slug import (
    GetCTShopBuySettingsUseCase,
    GetCTShopBuySettingsUseCaseProtocol,
)
from .adapters import get_character_service_client
from .repositories import (
    _get_city_trading_shop_buy_settings_repository,
    _get_city_trading_shop_settings_repository,
)


def get_city_trading_shop_buy_settings_service(
    repository: CityTradingShopBuySettingsRepositoryProtocol = Depends(_get_city_trading_shop_buy_settings_repository)
) -> CityTradingShopBuySettingsServiceProtocol:
    return CityTradingShopBuySettingsService(repository=repository)

def get_city_trading_shop_buy_settings_for_character_service(
    crud_service: CityTradingShopBuySettingsServiceProtocol = Depends(get_city_trading_shop_buy_settings_service),
    character_service: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> CityTradingShopBuySettingsForCharacterServiceProtocol:
    return CityTradingShopBuySettingsForCharacterService(
        crud_service=crud_service,
        character_service=character_service
    )

def get_get_ct_shop_buy_settings_use_case(
    service: CityTradingShopBuySettingsForCharacterServiceProtocol = Depends(get_city_trading_shop_buy_settings_for_character_service)
) -> GetCTShopBuySettingsUseCaseProtocol:
    return GetCTShopBuySettingsUseCase(service=service)


# city trading settings
def get_city_trading_shop_settings_service(repository: CityTradingShopSettingsRepositoryProtocol = Depends(_get_city_trading_shop_settings_repository)) -> CityTradingShopSettingsServiceProtocol:
    return CityTradingShopSettingsService(repository=repository)
