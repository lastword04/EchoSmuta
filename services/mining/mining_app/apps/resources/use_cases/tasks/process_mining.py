import uuid

from shared.schemas.base import StatusOkSchema

from .....core.use_cases import UseCaseProtocol
from ...services.mining_actions import ProcessMiningActionServiceProtocol


class ProcessMiningActionUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self, action_id: uuid.UUID, character: dict) -> StatusOkSchema:
        ...

class ProcessMiningActionUseCase(ProcessMiningActionUseCaseProtocol):
    def __init__(self, service: ProcessMiningActionServiceProtocol):
        self.service = service

    async def __call__(self, action_id: uuid.UUID, character: dict) -> StatusOkSchema:
        return await self.service.process_mining_action(action_id, character)