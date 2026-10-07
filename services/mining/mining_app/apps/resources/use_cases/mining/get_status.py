from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import MiningActionResponseSchema
from ...services.mining_actions import MiningActionServiceProtocol


class GetMiningStatusUseCaseProtocol(UseCaseProtocol[MiningActionResponseSchema]):
    async def __call__(self, user: UserTokenDataReadSchema) -> MiningActionResponseSchema:
        ...

class GetMiningStatusUseCase(GetMiningStatusUseCaseProtocol):
    def __init__(self, service: MiningActionServiceProtocol):
        self.service = service

    async def __call__(self, user: UserTokenDataReadSchema) -> MiningActionResponseSchema:
        if not user.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_proccessing_mining_action(user.character_id)