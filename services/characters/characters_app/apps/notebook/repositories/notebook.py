import uuid
import sqlalchemy as sa
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelFieldNotFoundException
from ..models import Notebook
from ..schemas import NotebookCreateDBSchema, NotebookUpdateDBSchema, NotebookReadSchema

class NotebookRepositoryProtocol(
    BaseRepositoryImpl[
        Notebook, 
        NotebookReadSchema, 
        NotebookCreateDBSchema, 
        NotebookUpdateDBSchema
    ]
):
    async def get_for_character(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        ...


class NotebookRepository(NotebookRepositoryProtocol):
    async def get_for_character(self: Self, character_id: uuid.UUID) -> NotebookReadSchema:
        async with self.session as s:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
            )
            model = (await s.execute(stmt)).scalar_one_or_none()

            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "character_id", character_id)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)
