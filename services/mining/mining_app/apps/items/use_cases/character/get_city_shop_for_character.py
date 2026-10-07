from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopResponseSchema
from ...services.city_trading_character.city_trading import (
    CityTradingShopCharacterServiceProtocol,
)


class GetCTShopForCharacterUseCaseProtocol(UseCaseProtocol[CityTradingShopResponseSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> CityTradingShopResponseSchema:
        ...


class GetCTShopForCharacterUseCase(GetCTShopForCharacterUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema, location_slug: str | None = None) -> CityTradingShopResponseSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_for_character(token.character_id, location_slug)