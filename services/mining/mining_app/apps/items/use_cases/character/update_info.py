import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopReadSchema, CityTradingShopUpdateInfoSchema
from ...services.city_trading_character.city_trading import (
    UpdateCityTradingShopServiceProtocol,
)


class UpdateInfoCTShopUseCaseProtocol(UseCaseProtocol[CityTradingShopReadSchema]):
    async def __call__(self: Self, id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, token: UserTokenDataReadSchema) -> CityTradingShopReadSchema:
        ...


class UpdateInfoCTShopUseCase(UpdateInfoCTShopUseCaseProtocol):
    def __init__(self: Self, service: UpdateCityTradingShopServiceProtocol):
        self.service = service

    async def __call__(self: Self, id: uuid.UUID, update_schema: CityTradingShopUpdateInfoSchema, token: UserTokenDataReadSchema) -> CityTradingShopReadSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.update_info(id, update_schema, token.character_id)