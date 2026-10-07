import uuid
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..services.notebook import NotebookCRUServiceProtocol
from ..schemas import (
    NotebookUpdateSchema,
    NotebookReadSchema
)

class UpdateNotebookUseCaseProtocol(UseCaseProtocol[NotebookReadSchema]):
    async def __call__(self: Self, notebook_id: uuid.UUID, data: NotebookUpdateSchema, character_id: uuid.UUID) -> NotebookReadSchema:
        ...

class UpdateNotebookUseCase(UpdateNotebookUseCaseProtocol):
    def __init__(self: Self, notebook_service: NotebookCRUServiceProtocol):
        self.notebook_service = notebook_service

    async def __call__(self: Self, notebook_id: uuid.UUID, data: NotebookUpdateSchema, character_id: uuid.UUID) -> NotebookReadSchema:
        return await self.notebook_service.update(notebook_id, data, character_id)