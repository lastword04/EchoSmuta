import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopResponseSchema
from ...services.city_trading_character.city_trading import (
    CityTradingShopCharacterServiceProtocol,
)


class GetCTShopByIdUseCaseProtocol(UseCaseProtocol[CityTradingShopResponseSchema]):
    async def __call__(self: Self, id: uuid.UUID, token: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        ...


class GetCTShopByIdUseCase(GetCTShopByIdUseCaseProtocol):
    def __init__(self: Self, service: CityTradingShopCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, id: uuid.UUID, token: UserTokenDataReadSchema) -> CityTradingShopResponseSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.get(id)