from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.captcha import CaptchaServiceProtocol
from shared.schemas.captcha import GeneratedCaptchaResponse

class CreateCaptchaUseCaseProtocol(UseCaseProtocol):
    async def __call__(self: Self) -> GeneratedCaptchaResponse:
        ...


class CreateCaptchaUseCase(CreateCaptchaUseCaseProtocol):
    """UseCase для создания капчи"""
    
    def __init__(self: Self, service: CaptchaServiceProtocol):
        self.service = service
    
    async def __call__(self: Self) -> GeneratedCaptchaResponse:
        """Создает капчу и возвращает ответ с ID и URL изображения"""
        return await self.service.create_captcha()