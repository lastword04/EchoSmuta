import uuid
from typing_extensions import Self
from shared.schemas.files import FileReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class GetFileUseCaseProtocol(UseCaseProtocol[FileReadSchema]):

    async def __call__(self: Self, id: uuid.UUID) -> FileReadSchema:
        ...


class GetFileUseCase(GetFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, id: uuid.UUID) -> FileReadSchema:
        return await self.file_managment_service.get(id)