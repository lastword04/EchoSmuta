from typing_extensions import Self
from shared.schemas.files import FileReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class GetByTemplateFileUseCaseProtocol(UseCaseProtocol[FileReadSchema]):

    async def __call__(self: Self, template: str) -> FileReadSchema:
        ...


class GetByTemplateFileUseCase(GetByTemplateFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, template: str) -> FileReadSchema:
        return await self.file_managment_service.get_by_template(template)