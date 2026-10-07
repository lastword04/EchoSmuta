from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...schemas import SlotRequestSchema, SlotReadSchema
from ...services.slots import CreateSlotServiceProtocol 


class CreateSlotUseCaseProtocol(UseCaseProtocol[SlotReadSchema]):
    async def __call__(self: Self, data: SlotRequestSchema, token: UserTokenDataReadSchema) -> SlotReadSchema:
        ...


class CreateSlotUseCase(CreateSlotUseCaseProtocol):
    def __init__(self: Self, service: CreateSlotServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: SlotRequestSchema, token: UserTokenDataReadSchema) -> SlotReadSchema:
        return await self.service.create(data, token.user_id)
