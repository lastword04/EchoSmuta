import json
import uuid
from typing import Protocol, Self

from fastapi import UploadFile

from shared.schemas.errors import BaseResponseSchema
from shared.schemas.files import FileReadSchema, FilesListReadSchema

from ....core.adapters.base_http import BaseHttpClientImpl


class FileServiceClientProtocol(Protocol):
    async def get(self: Self, id: uuid.UUID) -> FileReadSchema:
        """Получение файла по ID"""
        ...
    
    async def get_by_ids(self: Self, ids: list[uuid.UUID]) -> FilesListReadSchema:
        """Получение файлов по списку ID"""
        ...
    
class FileServiceClient(BaseHttpClientImpl, FileServiceClientProtocol):
    def __init__(
        self,
        base_url: str,  
        timeout: float = 15.0,  
        permissions: list[str] | None = None
    ):
        if permissions is None:
            permissions = ["files:read", "files:write"]
        super().__init__(
            base_url=base_url,
            target_service="file-service", 
            permissions=permissions,
            timeout=timeout
        )
    
    async def get(self: Self, id: uuid.UUID) -> FileReadSchema:
        """Получение файла по ID"""
        return await self.request(
            "GET",
            f"/{id}",
            response_model=FileReadSchema,
            error_model=BaseResponseSchema,
        )
    
    async def get_by_ids(self: Self, ids: list[uuid.UUID]) -> FilesListReadSchema:
        """Получение файлов по списку ID"""
        return await self.request(
            "POST",
            "/ids",
            json={'ids': [str(id) for id in ids]},
            response_model=FilesListReadSchema,
            error_model=BaseResponseSchema,
        )

    async def create_by_service(self: Self, data: dict, file: UploadFile | bytes, user_id: uuid.UUID) -> FileReadSchema:
        """Загрузка файла от имени сервиса через endpoint /by-service

        Поддерживает передачу как UploadFile, так и уже прочитанных байт (bytes).
        Если переданы байты, ожидается, что в data есть ключ 'filename'.
        """
        # Поддержка UploadFile и bytes
        if hasattr(file, 'read'):
            content = await file.read()
            filename = getattr(file, 'filename', 'file')
            content_type = getattr(file, 'content_type', 'application/octet-stream') or 'application/octet-stream'
        else:
            # Ожидаем bytes
            content = file
            filename = data.get('filename', 'file')
            content_type = data.get('content_type', 'application/octet-stream')

        # Отправляем data как JSON в поле form-data
        return await self.request(
            "POST",
            "/by-service",
            params={'user_id': str(user_id)},
            data={"data": json.dumps(data)},
            files={"file": (filename, content, content_type)},
            response_model=FileReadSchema,
            error_model=BaseResponseSchema,
        )