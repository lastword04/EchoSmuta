import uuid
from shared.schemas.base import StatusOkSchema
from ....core.use_cases import UseCaseProtocol
from ..services.buff_service import BuffServiceProtocol


class RemoveBuffUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self, character_id: uuid.UUID, buff_type: str) -> StatusOkSchema: ...


class RemoveBuffUseCase(RemoveBuffUseCaseProtocol):
    def __init__(self, service: BuffServiceProtocol):
        self.service = service

    async def __call__(self, character_id: uuid.UUID, buff_type: str) -> StatusOkSchema:
        await self.service.remove_buff(character_id, buff_type)
        return StatusOkSchema()