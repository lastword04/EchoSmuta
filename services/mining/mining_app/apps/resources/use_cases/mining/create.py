from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.captcha import CaptchaVerificationRequest

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import MiningActionReadSchema
from ...services.mining_actions import ValidateCreateMiningActionServiceProtocol


class CreateMiningActionUseCaseProtocol(UseCaseProtocol[MiningActionReadSchema]):
    async def __call__(self, user: UserTokenDataReadSchema, captcha: CaptchaVerificationRequest) -> MiningActionReadSchema:
        ...

class CreateMiningActionUseCase(CreateMiningActionUseCaseProtocol):
    def __init__(self, service: ValidateCreateMiningActionServiceProtocol):
        self.service = service

    async def __call__(self, user: UserTokenDataReadSchema, captcha: CaptchaVerificationRequest) -> MiningActionReadSchema:
        if not user.character_id:
            raise PermissionDeniedError()

        return await self.service.validate_captcha_and_mine(user.character_id, captcha)