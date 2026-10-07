import uuid

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import MiningActionReadSchema
from ...services.mining_actions import MiningActionServiceProtocol


class GetMiningActionUseCaseProtocol(UseCaseProtocol[MiningActionReadSchema]):
    async def __call__(self, action_id: uuid.UUID, user: UserTokenDataReadSchema) -> MiningActionReadSchema:
        ...

class GetMiningActionUseCase(GetMiningActionUseCaseProtocol):
    def __init__(self, service: MiningActionServiceProtocol):
        self.service = service

    async def __call__(self, action_id: uuid.UUID, user: UserTokenDataReadSchema) -> MiningActionReadSchema:
        if not user.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_for_character(action_id, user.character_id)