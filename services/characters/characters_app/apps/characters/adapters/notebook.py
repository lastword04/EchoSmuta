import uuid
from typing import Protocol
from typing_extensions import Self
from ....apps.notebook.schemas import NotebookReadSchema
from ....apps.notebook.services.notebook import NotebookCRUServiceProtocol

class CreateNotebookAdapterProtocol(Protocol):
    async def create(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        ...

class CreateNotebookAdapter(CreateNotebookAdapterProtocol):
    def __init__(self: Self, notebook_service: NotebookCRUServiceProtocol):
        self.notebook_service = notebook_service

    async def create(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        return await self.notebook_service.create(character_id)