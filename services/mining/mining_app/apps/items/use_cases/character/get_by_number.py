from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopResponseSchema
from ...services.city_trading_character.city_trading import (
    CityTradingShopCharacterServiceProtocol,
)


class GetCTShopByNumberUseCaseProtocol(UseCaseProtocol[CityTradingShopResponseSchema]):
    async def __call__(self: Self, number: int, token: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        ...


class GetCTShopByNumberUseCase(GetCTShopByNumberUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, number: int, token: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get_by_number(token.character_id, number)