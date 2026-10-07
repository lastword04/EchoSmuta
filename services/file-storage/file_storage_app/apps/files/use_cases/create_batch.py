import json
from fastapi import UploadFile
from typing_extensions import Self
from shared.schemas.files import FilesListReadSchema, FileListCreateSchema
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class CreateBatchFileUseCaseProtocol(UseCaseProtocol[FilesListReadSchema]):

    async def __call__(self: Self, data: str, files: list[UploadFile]) -> FilesListReadSchema:
        ...


class CreateBatchFileUseCase(CreateBatchFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, data: str, files: list[UploadFile], token: UserTokenDataReadSchema) -> FilesListReadSchema:
        schema = FileListCreateSchema(**json.loads(data))
        return await self.file_managment_service.create_batch(schema.files, files, token.user_id)