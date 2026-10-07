import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import CityTradingShopUpdatePhotoSchema
from ...services.city_trading_character.city_trading import (
    UpdateCityTradingShopServiceProtocol,
)


class UpdatePhotoCTShopUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, id: uuid.UUID, update_schema: CityTradingShopUpdatePhotoSchema, token: UserTokenDataReadSchema) -> StatusOkSchema:
        ...


class UpdatePhotoCTShopUseCase(UpdatePhotoCTShopUseCaseProtocol):
    def __init__(self: Self, service: UpdateCityTradingShopServiceProtocol):
        self.service = service

    async def __call__(self: Self, id: uuid.UUID, update_schema: CityTradingShopUpdatePhotoSchema, token: UserTokenDataReadSchema) -> StatusOkSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.service.update_photo(id, update_schema, token.character_id)