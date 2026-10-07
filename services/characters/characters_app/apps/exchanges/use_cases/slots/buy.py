import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...schemas import BuySlotResponse
from ...services.slots import BuySlotServiceProtocol 


class BuySlotUseCaseProtocol(UseCaseProtocol[BuySlotResponse]):
    async def __call__(self: Self, slot_id: uuid.UUID, token: UserTokenDataReadSchema) -> BuySlotResponse:
        ...


class BuySlotUseCase(BuySlotUseCaseProtocol):
    def __init__(self: Self, service: BuySlotServiceProtocol):
        self.service = service

    async def __call__(self: Self, slot_id: uuid.UUID, token: UserTokenDataReadSchema) -> BuySlotResponse:
        return await self.service.buy(slot_id, token.user_id)
