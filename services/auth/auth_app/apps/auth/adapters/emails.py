from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.email import EmailResetPasswordSchema, EmailLogReadSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class EmailServiceClientProtocol(Protocol):
    async def send_reset_password(self: Self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        """Отправление email о сбросе пароля"""
        ...


class EmailServiceClient(BaseHttpClientImpl, EmailServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] = ["emails:read", "emails:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="email-service",
            permissions=permissions,
            timeout=timeout
        )

    async def send_reset_password(self: Self, email: EmailResetPasswordSchema) -> EmailLogReadSchema:
        """Отправление email о сбросе пароля"""

        return await self.request(
            "POST",
            "/reset-password",
            response_model=EmailLogReadSchema,
            error_model=BaseResponseSchema,
            json=email.model_dump(mode='json'),
        )