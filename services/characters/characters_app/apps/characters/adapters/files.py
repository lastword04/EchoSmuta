from typing import Protocol
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.files import FileReadSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class FileServiceClientProtocol(Protocol):
    async def get_by_template(self, template: str) -> FileReadSchema:
        """Получение картинки по шаблонному имени"""
        ...


class FileServiceClient(BaseHttpClientImpl, FileServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 30.0,  
        permissions: list[str] = ["files:read", "files:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="file-service",
            permissions=permissions,
            timeout=timeout
        )

    async def get_by_template(self, template: str) -> FileReadSchema:
        """Получение картинки по шаблонному имени"""


        return await self.request(
            "GET",
            f"/template_name/{template}",
            response_model=FileReadSchema,
            error_model=BaseResponseSchema,
        )