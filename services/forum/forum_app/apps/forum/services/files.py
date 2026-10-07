from typing_extensions import Self
from ..repositories.files import FileRepositoryProtocol
from ..schemas import FileCreateSchema, FileReadSchema
from typing import Protocol


class FileServiceProtocol(Protocol):
    async def create(self: Self, create_object: FileCreateSchema) -> FileReadSchema:
        ...

    async def bulk_create(self: Self, create_object: list[FileCreateSchema]) -> list[FileReadSchema]:
        ...


class FileService(FileServiceProtocol):
    def __init__(self: Self, repository: FileRepositoryProtocol):
        self.repository = repository

    async def create(self: Self, create_object: FileCreateSchema) -> FileReadSchema:
        return await self.repository.create(create_object)
    
    async def bulk_create(self: Self, create_object: list[FileCreateSchema]) -> list[FileReadSchema]:
        return await self.repository.bulk_create(create_object)