from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopBuySettingsReadSchema
from ...services.settings.city_trading_shop_buy_settings import (
    CityTradingShopBuySettingsForCharacterServiceProtocol,
)


class GetCTShopBuySettingsUseCaseProtocol(UseCaseProtocol[CityTradingShopBuySettingsReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CityTradingShopBuySettingsReadSchema:
        ...


class GetCTShopBuySettingsUseCase(GetCTShopBuySettingsUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopBuySettingsForCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CityTradingShopBuySettingsReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_by_character_id(token.character_id)