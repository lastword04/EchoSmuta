from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.base import StatusOkSchema
from shared.schemas.captcha import CaptchaVerificationRequest
from ....core.adapters.base_http import BaseHttpClientImpl

class CaptchaServiceClientProtocol(Protocol):
    async def verify_captcha(self: Self, captcha: CaptchaVerificationRequest) -> StatusOkSchema:
        """Отправление email о сбросе пароля"""
        ...


class CaptchaServiceClient(BaseHttpClientImpl, CaptchaServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] = ["captcha:read", "captcha:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="captcha-service",
            permissions=permissions,
            timeout=timeout
        )

    async def verify_captcha(self: Self, captcha: CaptchaVerificationRequest) -> StatusOkSchema:
        """Отправление email о сбросе пароля"""

        return await self.request(
            "POST",
            "/verify",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=captcha.model_dump(mode='json'),
        )