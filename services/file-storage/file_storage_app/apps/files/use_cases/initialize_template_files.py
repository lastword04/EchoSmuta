from fastapi import UploadFile
from typing_extensions import Self
from shared.schemas.files import FileReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import DefaultTemplateFilesGeneratorProtocol


class CreateIfNotExistFilesUseCaseProtocol(UseCaseProtocol[list[FileReadSchema]]):

    async def __call__(self: Self, data: str, file: UploadFile) -> list[FileReadSchema]:
        ...


class CreateIfNotExistFilesUseCase(CreateIfNotExistFilesUseCaseProtocol):

    def __init__(self: Self, generator: DefaultTemplateFilesGeneratorProtocol):
        self.generator = generator

    async def __call__(self: Self) -> list[FileReadSchema]:
        return await self.generator.create_template_files_if_not_exist()