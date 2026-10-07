import json
from fastapi import UploadFile
from typing_extensions import Self
from shared.schemas.files import FileReadSchema, FileCreateSchema
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class CreateFileUseCaseProtocol(UseCaseProtocol[FileReadSchema]):

    async def __call__(self: Self, data: str, file: UploadFile,  user: UserTokenDataReadSchema) -> FileReadSchema:
        ...


class CreateFileUseCase(CreateFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, data: str, file: UploadFile, user: UserTokenDataReadSchema) -> FileReadSchema:
        schema = FileCreateSchema(**json.loads(data))
        return await self.file_managment_service.create(schema, file, user.user_id)