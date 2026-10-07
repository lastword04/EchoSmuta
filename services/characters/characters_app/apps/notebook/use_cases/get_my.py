import uuid
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.notebook import NotebookCRUServiceProtocol
from ..schemas import (
    NotebookReadSchema
)

class GetMyNotebookUseCaseProtocol(UseCaseProtocol[NotebookReadSchema]):
    async def __call__(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        ...

class GetMyNotebookUseCase(GetMyNotebookUseCaseProtocol):
    def __init__(self: Self, notebook_service: NotebookCRUServiceProtocol):
        self.notebook_service = notebook_service

    async def __call__(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        return await self.notebook_service.get_for_character(character_id)