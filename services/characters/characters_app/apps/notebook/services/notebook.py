import uuid
from typing import Protocol
from typing_extensions import Self
from ....core.utils.exceptions import ModelNotFoundException
from ..models import Notebook
from ..repositories.notebook import NotebookRepositoryProtocol
from ..schemas  import(
    NotebookCreateDBSchema,
    NotebookUpdateSchema,
    NotebookUpdateDBSchema,
    NotebookReadSchema
)


class NotebookCRUServiceProtocol(Protocol):
    async def create(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        ...
    
    async def update(self: Self, notebook_id: uuid.UUID, data: NotebookUpdateSchema, character_id: uuid.UUID) -> NotebookReadSchema:
        ...

    async def get_for_character(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        ...
    
class NotebookCRUService(NotebookCRUServiceProtocol):
    def __init__(self: Self, repository: NotebookRepositoryProtocol):
        self.repository = repository
    
    async def create(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        db_notebook = NotebookCreateDBSchema(
            character_id=character_id,
        )
        return await self.repository.create(db_notebook)
    
    async def update(self: Self, notebook_id: uuid.UUID, data: NotebookUpdateSchema, character_id: uuid.UUID) -> NotebookReadSchema:
        notebook = await self.repository.get(notebook_id)
        if notebook.character_id != character_id:
            raise ModelNotFoundException(Notebook, notebook_id)
        db_notebook = NotebookUpdateDBSchema(
            **data.model_dump(exclude={"id"}),
            id=notebook_id,
            character_id=character_id,
        )
        return await self.repository.update(db_notebook)
    
    async def get_for_character(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        return await self.repository.get_for_character(character_id)

