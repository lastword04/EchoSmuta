"""Провайдеры лицензии на крафт (crafting_license-домен).

Репозиторий лицензии шарится с character-доменом, поэтому его провайдер
лежит в deps/repositories.py.
"""
from fastapi import Depends

from ..adapters.characters import CharacterServiceClientProtocol
from ..events.items import ItemEventsProtocol
from ..repositories.crafting_license.crafting_license import (
    CraftingLicenseRepositoryProtocol,
)
from ..repositories.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsRepositoryProtocol,
)
from ..services.adapters.item_templates import ItemTemplateServiceProtocol
from ..services.crafting_license.crafting_license import (
    CraftingLicenseService,
    CraftingLicenseServiceProtocol,
)
from ..use_cases.crafting_license.buy import (
    BuyCraftingLicenseUseCase,
    BuyCraftingLicenseUseCaseProtocol,
)
from ..use_cases.crafting_license.get_status import (
    GetCraftingLicenseStatusUseCase,
    GetCraftingLicenseStatusUseCaseProtocol,
)
from ..use_cases.crafting_license.renew import (
    RenewCraftingLicenseUseCase,
    RenewCraftingLicenseUseCaseProtocol,
)
from .adapters import get_character_service_client, get_item_template_service
from .events import get_items_events
from .repositories import (
    _get_city_trading_shop_buy_settings_repository,
    _get_crafting_license_repository,
)


# service
def get_crafting_license_service(
    repo: CraftingLicenseRepositoryProtocol = Depends(_get_crafting_license_repository),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client),
    template_service: ItemTemplateServiceProtocol = Depends(get_item_template_service),
    items_events: ItemEventsProtocol = Depends(get_items_events),
    city_settings_buy_repo: CityTradingShopBuySettingsRepositoryProtocol = Depends(_get_city_trading_shop_buy_settings_repository),
) -> CraftingLicenseServiceProtocol:
    return CraftingLicenseService(
        repo=repo,
        character_client=character_client,
        template_service=template_service,
        items_events=items_events,
        city_settings_buy_repo=city_settings_buy_repo,
    )

# use cases
def get_get_crafting_license_status_use_case(
    service: CraftingLicenseServiceProtocol = Depends(get_crafting_license_service)
) -> GetCraftingLicenseStatusUseCaseProtocol:
    return GetCraftingLicenseStatusUseCase(service=service)

def get_buy_crafting_license_use_case(
    service: CraftingLicenseServiceProtocol = Depends(get_crafting_license_service)
) -> BuyCraftingLicenseUseCaseProtocol:
    return BuyCraftingLicenseUseCase(service=service)

def get_renew_crafting_license_use_case(
    service: CraftingLicenseServiceProtocol = Depends(get_crafting_license_service)
) -> RenewCraftingLicenseUseCaseProtocol:
    return RenewCraftingLicenseUseCase(service=service)
