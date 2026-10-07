from typing import Protocol

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopResponseSchema
from ...services.city_trading_character.city_trading import (
    UpdateCityTradingShopServiceProtocol,
)


class LevelUpCTShopUseCaseProtocol(Protocol):
    async def __call__(self, user: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        ...


class LevelUpCTShopUseCase(LevelUpCTShopUseCaseProtocol):
    def __init__(self, service: UpdateCityTradingShopServiceProtocol):
        self.service = service

    async def __call__(self, user: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        if not user.character_id:
            raise PermissionDeniedError()
        return await self.service.level_up_shop(user.character_id)
