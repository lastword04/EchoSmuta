from uuid import uuid4
from typing import Protocol, Optional
import logging
from typing_extensions import Self
from shared.schemas.base import StatusOkSchema
from ..repositories.captcha_repository import CaptchaRedisRepository
from ..generators.captcha_generator import CaptchaGeneratorProtocol
from shared.schemas.captcha import GeneratedCaptchaResponse, CaptchaVerificationRequest
from ..exceptions import CaptchaExpiredError, InvalidCaptchaInputError

# Настройка логгера
logger = logging.getLogger(__name__)

class CaptchaServiceProtocol(Protocol):
    async def create_captcha(self: Self) -> GeneratedCaptchaResponse:
        ...

    async def get_captcha(self: Self, captcha_id: str) -> Optional[str]:
        ...

    async def verify_captcha(self: Self, data: CaptchaVerificationRequest) -> StatusOkSchema:
        ...


class CaptchaService(CaptchaServiceProtocol):
    """Сервис для работы с капчей"""
    
    def __init__(self: Self, 
                 repository: CaptchaRedisRepository, 
                 generator: CaptchaGeneratorProtocol,
                 ttl: int = 300):
        self.repository = repository
        self.generator = generator
        self.ttl = ttl  # Время жизни капчи в секундах
        logger.info(f"CaptchaService initialized with TTL={ttl} seconds")
    
    async def create_captcha(self: Self) -> GeneratedCaptchaResponse:
        """Создает и сохраняет капчу, возвращает ID капчи"""
        logger.debug("Starting captcha creation")
        
        try:
            captcha = self.generator.generate_captcha()
            captcha_id = str(uuid4())
            
            logger.debug(f"Generated captcha text: {captcha.text[:1]}*** (ID: {captcha_id[:8]}...)")
            
            await self.repository.set(captcha_id, captcha.text, ttl=self.ttl)
            logger.info(f"Successfully created captcha with ID: {captcha_id[:8]}...")
            
            response = GeneratedCaptchaResponse(
                captcha_id=captcha_id,
                image_url=captcha.data_url
            )
            
            logger.debug("Captcha creation completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create captcha: {str(e)}", exc_info=True)
            raise

    async def get_captcha(self: Self, captcha_id: str) -> Optional[str]:
        """Получает текст капчи по ID"""
        logger.debug(f"Retrieving captcha with ID: {captcha_id[:8]}...")
        
        try:
            stored_text = await self.repository.get(captcha_id)
            
            if stored_text is None:
                logger.info(f"Captcha not found or expired: {captcha_id[:8]}...")
            else:
                logger.debug(f"Successfully retrieved captcha: {captcha_id[:8]}...")
                
            return stored_text
            
        except Exception as e:
            logger.error(f"Failed to retrieve captcha {captcha_id[:8]}: {str(e)}", exc_info=True)
            raise

    async def verify_captcha(self: Self, data: CaptchaVerificationRequest) -> StatusOkSchema:
        """Проверяет введенный пользователем текст капчи"""
        logger.info(f"Starting captcha verification for ID: {data.captcha_id[:8]}...")
        
        try:
            stored_text = await self.get_captcha(data.captcha_id)
            
            if stored_text is None:
                logger.warning(f"Captcha verification failed: captcha expired or not found (ID: {data.captcha_id[:8]}...)")
                raise CaptchaExpiredError()
            
            # Проверяем без учета регистра
            is_valid = stored_text.lower() == data.user_input.lower()
            logger.debug(f"Captcha comparison - stored: {stored_text[:1]}***, user_input: {data.user_input[:3]}***, valid: {is_valid}")
            
            if is_valid:
                # Удаляем капчу после успешной проверки (одноразовая)
                await self.repository.delete(data.captcha_id)
                logger.info(f"Captcha verification successful, captcha deleted (ID: {data.captcha_id[:8]}...)")
                return StatusOkSchema()
            else:
                logger.warning(f"Captcha verification failed: invalid input (ID: {data.captcha_id[:8]}...)")
                raise InvalidCaptchaInputError()
                
        except (CaptchaExpiredError, InvalidCaptchaInputError):
            # Эти ошибки уже залогированы выше, просто пробрасываем
            raise
        except Exception as e:
            logger.error(f"Unexpected error during captcha verification (ID: {data.captcha_id[:8]}...): {str(e)}", exc_info=True)
            raise