from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.chat import ChatSettingsReadSchema, ChatSettingsDefaultCreateSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class ChatSettingsServiceClientProtocol(Protocol):
    async def create_default(self: Self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        """Создание настроек чата для персонажа по умолчанию"""
        ...


class ChatSettingsServiceClient(BaseHttpClientImpl, ChatSettingsServiceClientProtocol):
    def __init__(
        self,
        base_url: str,
        timeout: float = 120.0,
        permissions: list[str] = ["chat:read", "chat:write"]
    ):
        super().__init__(
            base_url=base_url,
            target_service="chat-service",
            permissions=permissions,
            timeout=timeout
        )

    async def create_default(self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        """Создание настроек чата для персонажа по умолчанию"""

        return await self.request(
            "POST",
            "/settings/default",
            json=data.model_dump(mode="json"),
            response_model=ChatSettingsReadSchema,
            error_model=BaseResponseSchema,
        )