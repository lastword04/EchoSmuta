from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.rest_service import RestServiceProtocol


class ExpireRestRentalsUseCaseProtocol(UseCaseProtocol[int]):
    async def __call__(self: Self) -> int: ...


class ExpireRestRentalsUseCase(ExpireRestRentalsUseCaseProtocol):
    def __init__(
        self,
        service: RestServiceProtocol       
    ):
        self.service = service        

    async def __call__(self) -> int:
        character_ids = await self.service.expire_rentals()
        return len(character_ids)