import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from ....core.utils.exceptions import ModelAlreadyExistsError
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import File
from ..schemas import (
    FileCreateSchema,
    FileUpdateSchema,
    FileReadSchema
)  

class FileRepositoryProtocol(BaseRepositoryImpl[File, FileReadSchema, FileCreateSchema, FileUpdateSchema]):
    pass

class FileRepository(FileRepositoryProtocol):
    async def create(self, create_object: FileCreateSchema) -> FileReadSchema:
        """Create single record"""
        try:
            async with self.session as s, s.begin():
                stmt = (
                    sa.insert(self.model_type)
                    .values(**create_object.model_dump())
                    .returning(self.model_type)
                )
                model = (await s.execute(stmt)).scalar_one()
                return self.read_schema_type.model_validate(model, from_attributes=True)
        except IntegrityError as e:
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                field_name = self._extract_field_name(str(e), type(create_object))
                raise ModelAlreadyExistsError(self.model_type, field_name, f"duplicate key for field: {field_name}")
            raise