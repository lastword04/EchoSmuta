import uuid
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import Ignore
from ..schemas import IgnoreCreateSchema, IgnoreReadSchema, IgnoreUpdateSchema

class IgnoreRepositoryProtocol(BaseRepositoryImpl[Ignore, IgnoreReadSchema, IgnoreCreateSchema, IgnoreUpdateSchema]):
    async def get_ignored_characters(self: Self, character_id: uuid.UUID, other_character_ids: list[uuid.UUID]) -> dict[uuid.UUID, bool]:
        ...

    async def delete(self: Self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        ...

class IgnoreRepository(IgnoreRepositoryProtocol):
    async def get_ignored_characters(self: Self, character_id: uuid.UUID, other_character_ids: list[uuid.UUID]) -> dict[uuid.UUID, bool]:
        """
        Возвращает словарь {ignored_character_id: True}, если они игнорируются character_id.
        """
        async with self.session as session:
            stmt = sa.select(self.model_type.ignored_character_id).where(
                self.model_type.character_id == character_id,
                self.model_type.ignored_character_id.in_(other_character_ids)
            )
            result = await session.execute(stmt)
            ignored_ids = [row[0] for row in result.fetchall()]
            return {ignored_id: True for ignored_id in ignored_ids}
        

    def _orm_to_dict(self, obj):
        """Конвертирует ORM-модель SQLAlchemy в словарь для Pydantic-валидации."""
        return {c.key: getattr(obj, c.key) for c in inspect(obj.__class__).mapper.column_attrs}
    

    async def create(self: Self, data: IgnoreCreateSchema) -> IgnoreReadSchema:
        """
        Создаёт запись игнора. Если запись уже существует (unique constraint)
        — возвращает существующую (идемпотентное поведение, защита от рассинхрона UI/БД).
        """
        async with self.session as session, session.begin():
            new_ignore = self.model_type(**data.model_dump())
            session.add(new_ignore)
            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
                # Запись уже есть — возвращаем существующую
                stmt = sa.select(self.model_type).where(
                    self.model_type.character_id == data.character_id,
                    self.model_type.ignored_character_id == data.ignored_character_id
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing is None:
                    raise  # IntegrityError по другой причине — пробрасываем
                return IgnoreReadSchema.model_validate(self._orm_to_dict(existing))
            return IgnoreReadSchema.model_validate(self._orm_to_dict(new_ignore))

    async def delete(self: Self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = sa.delete(self.model_type).where(
                self.model_type.character_id == character_id,
                self.model_type.ignored_character_id == ignored_character_id
            )
            result = await session.execute(stmt)
            return result.rowcount > 0