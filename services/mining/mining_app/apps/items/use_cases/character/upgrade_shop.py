import uuid
from typing import Protocol

from ...schemas import CityTradingShopResponseSchema


class UpgradeCTShopUseCaseProtocol(Protocol):
    async def __call__(self, id: uuid.UUID, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        ...


class UpgradeCTShopUseCase(UpgradeCTShopUseCaseProtocol):
    def __init__(self, service):
        self.service = service

    async def __call__(self, id: uuid.UUID, character_id: uuid.UUID) -> CityTradingShopResponseSchema:
        return await self.service.upgrade_shop(id, character_id)
