import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.use_cases import UseCaseProtocol
from ..services.file_managment_service import FileManagmentServiceProtocol


class DeleteFileUseCaseProtocol(UseCaseProtocol[bool]):

    async def __call__(self: Self, id: uuid.UUID) -> bool:
        ...


class DeleteFileUseCase(DeleteFileUseCaseProtocol):

    def __init__(self: Self, file_managment_service: FileManagmentServiceProtocol):
        self.file_managment_service = file_managment_service

    async def __call__(self: Self, id: uuid.UUID, token: UserTokenDataReadSchema) -> bool:
        return await self.file_managment_service.delete(id, token.user_id)