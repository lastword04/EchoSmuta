from typing import Protocol, Self

from shared.schemas.base import StatusOkSchema
from shared.schemas.captcha import CaptchaVerificationRequest
from shared.schemas.errors import BaseResponseSchema

from ....core.adapters.base_http import BaseHttpClientImpl


class CaptchaServiceClientProtocol(Protocol):
    async def verify_captcha(self: Self, captcha: CaptchaVerificationRequest) -> StatusOkSchema:
        """Verify captcha with captcha service"""
        ...


class CaptchaServiceClient(BaseHttpClientImpl, CaptchaServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] | None = None
    ):
        if permissions is None:
            permissions = ["captcha:read", "captcha:write"]
        super().__init__(
            base_url=base_url,
            target_service="captcha-service",
            permissions=permissions,
            timeout=timeout
        )

    async def verify_captcha(self: Self, captcha: CaptchaVerificationRequest) -> StatusOkSchema:
        """Verify captcha with captcha service"""

        return await self.request(
            "POST",
            "/verify",
            response_model=StatusOkSchema,
            error_model=BaseResponseSchema,
            json=captcha.model_dump(mode='json'),
        )
