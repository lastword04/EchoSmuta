from typing_extensions import Self
from shared.schemas.files import FileIdsSchema, FilesListReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class GetIdsFileUseCaseProtocol(UseCaseProtocol[FilesListReadSchema]):

    async def __call__(self: Self, ids: FileIdsSchema) -> FilesListReadSchema:
        ...


class GetIdsFileUseCase(GetIdsFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, ids: FileIdsSchema) -> FilesListReadSchema:
        return await self.file_managment_service.get_by_ids(ids)