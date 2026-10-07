import uuid
from shared.schemas.base import StatusOkSchema
from ....core.use_cases import UseCaseProtocol
from ..schemas import ApplyBuffSchema
from ..services.buff_service import BuffServiceProtocol


class ApplyBuffUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self, data: ApplyBuffSchema) -> StatusOkSchema: ...


class ApplyBuffUseCase(ApplyBuffUseCaseProtocol):
    def __init__(self, service: BuffServiceProtocol):
        self.service = service

    async def __call__(self, data: ApplyBuffSchema) -> StatusOkSchema:
        await self.service.apply_buff(data)
        return StatusOkSchema()