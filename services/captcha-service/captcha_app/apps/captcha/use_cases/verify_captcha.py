from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.captcha import CaptchaServiceProtocol
from shared.schemas.captcha import CaptchaVerificationRequest
from shared.schemas.base import StatusOkSchema

class VerifyCaptchaUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self: Self, data: CaptchaVerificationRequest) -> StatusOkSchema:
        ...


class VerifyCaptchaUseCase(VerifyCaptchaUseCaseProtocol):
    """UseCase для создания капчи"""
    
    def __init__(self: Self, service: CaptchaServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: CaptchaVerificationRequest) -> StatusOkSchema:
        """Создает капчу и возвращает ответ с ID и URL изображения"""
        return await self.service.verify_captcha(data)