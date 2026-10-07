from typing import Protocol
from typing_extensions import Self
from shared.schemas.errors import BaseResponseSchema
from shared.schemas.files import FileIdsSchema, FilesListReadSchema
from ....core.adapters.base_http import BaseHttpClientImpl

class FileServiceClientProtocol(Protocol):
    async def get_by_ids(self: Self, files_ids: FileIdsSchema) -> FilesListReadSchema:
        """Получение файлов по ID"""
        ...
    
class FileServiceClient(BaseHttpClientImpl, FileServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] = ["files:read", "files:write"] 
    ):
        super().__init__(
            base_url=base_url,
            target_service="file-service", 
            permissions=permissions,
            timeout=timeout
        )
    
    async def get_by_ids(self: Self, files_ids: FileIdsSchema) -> FilesListReadSchema:
        """Получение файлов по ID"""
        return await self.request(
            "POST",
            "/ids",
            response_model=FilesListReadSchema,
            error_model=BaseResponseSchema,
            json=files_ids.model_dump(mode='json'),
        )
    