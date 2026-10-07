import json
import uuid
from fastapi import UploadFile
from typing_extensions import Self
from shared.schemas.files import FileReadSchema, FileCreateSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class CreateFileByServiceUseCaseProtocol(UseCaseProtocol[FileReadSchema]):

    async def __call__(self: Self, data: str, file: UploadFile,  user_id: uuid.UUID) -> FileReadSchema:
        ...


class CreateFileByServiceUseCase(CreateFileByServiceUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, data: str, file: UploadFile, user_id: uuid.UUID) -> FileReadSchema:
        schema = FileCreateSchema(**json.loads(data))
        return await self.file_managment_service.create(schema, file, user_id)