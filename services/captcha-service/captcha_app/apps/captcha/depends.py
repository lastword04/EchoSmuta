import redis.asyncio as redis
from fastapi import Depends
from captcha.image import ImageCaptcha
from ...core.redis import get_redis_client
from ...settings import Settings, get_settings
from .repositories.captcha_repository import CaptchaRedisRepositoryProtocol, CaptchaRedisRepository
from .generators.captcha_generator import CaptchaGeneratorProtocol, CaptchaGenerator
from .services.captcha import CaptchaServiceProtocol, CaptchaService
from .use_cases.create_captcha import CreateCaptchaUseCaseProtocol, CreateCaptchaUseCase
from .use_cases.verify_captcha import VerifyCaptchaUseCaseProtocol, VerifyCaptchaUseCase

def __get_captcha_redis_repository(redis_client: redis.Redis = Depends(get_redis_client)) -> CaptchaRedisRepositoryProtocol:
    """
    Получает репозиторий для работы с капчей.
    """
    return CaptchaRedisRepository(redis_client)

def get_image_generator(settings: Settings = Depends(get_settings)) -> ImageCaptcha:
    return ImageCaptcha(fonts=[settings.image.font_path])


def get_captcha_generator(image_generator: ImageCaptcha = Depends(get_image_generator)) -> CaptchaGeneratorProtocol:
    """
    Получает генератор для работы с капчей.
    """
    return CaptchaGenerator(generator=image_generator)

def get_captcha_service(
    repository: CaptchaRedisRepositoryProtocol = Depends(__get_captcha_redis_repository),
    generator: CaptchaGeneratorProtocol = Depends(get_captcha_generator),
    settings: Settings = Depends(get_settings),
) -> CaptchaServiceProtocol:
    """
    Получает сервис для работы с капчей.
    """
    return CaptchaService(repository, generator, settings.redis_ttl)


def get_captcha_create_use_case(
    service: CaptchaServiceProtocol = Depends(get_captcha_service)
) -> CreateCaptchaUseCaseProtocol:
    """
    Получает UseCase для создания капчи.
    """
    return CreateCaptchaUseCase(service)


def get_captcha_verify_use_case(
    service: CaptchaServiceProtocol = Depends(get_captcha_service)
) -> VerifyCaptchaUseCaseProtocol:
    """
    Получает UseCase для верификации капчи.
    """
    return VerifyCaptchaUseCase(service)
