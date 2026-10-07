from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.house_guest_service import HouseGuestServiceProtocol


class ExpireHouseRequestsUseCaseProtocol(UseCaseProtocol[int]):
    async def __call__(self: Self) -> int:
        ...


class ExpireHouseRequestsUseCase(ExpireHouseRequestsUseCaseProtocol):
    def __init__(self: Self, service: HouseGuestServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> int:
        return await self.service.expire_requests()