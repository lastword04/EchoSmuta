import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from typing import Optional
from typing_extensions import Self
from ....core.utils.exceptions import ModelAlreadyExistsError
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..schemas import FileCreateDBSchema, FileUpdateDBSchema, FileReadDBSchema
from ..models import File

class FileRepositoryProtocol(BaseRepositoryImpl[
    File,
    FileReadDBSchema,
    FileCreateDBSchema,
    FileUpdateDBSchema
]):
    async def get_by_template(self: Self, template: str) -> Optional[FileReadDBSchema]:
        ...


class FileRepository(FileRepositoryProtocol):
    async def create(self, create_object: FileCreateDBSchema) -> FileReadDBSchema:
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

    async def get_by_template(self: Self, template: str) -> Optional[FileReadDBSchema]:
        async with self.session as s:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.template_name == template)
            )

            model = (await s.execute(stmt)).scalar_one_or_none()

            if model is None:
                return None
            
            return FileReadDBSchema.model_validate(model, from_attributes=True)

