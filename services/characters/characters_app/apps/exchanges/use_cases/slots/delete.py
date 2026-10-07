import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.slots import DeleteSlotServiceProtocol 


class DeleteSlotUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, slot_id: uuid.UUID, token: UserTokenDataReadSchema) -> None:
        ...


class DeleteSlotUseCase(DeleteSlotUseCaseProtocol):
    def __init__(self: Self, service: DeleteSlotServiceProtocol):
        self.service = service

    async def __call__(self: Self, slot_id: uuid.UUID, token: UserTokenDataReadSchema) -> None:
        await self.service.delete(slot_id, token.user_id)
