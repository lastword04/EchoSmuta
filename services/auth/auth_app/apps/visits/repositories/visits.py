import uuid
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException
from ..models import NewUsersVisit
from ..schemas import NewUsersVisitCreateSchema, NewUsersVisitReadSchema, NewUsersVisitUpdateSchema

class NewUsersVisitRepositoryProtocol(BaseRepositoryImpl[
    NewUsersVisit,
    NewUsersVisitReadSchema,
    NewUsersVisitCreateSchema,
    NewUsersVisitUpdateSchema
]):
    async def register(self: Self, visit_id: uuid.UUID, character_id: uuid.UUID, refferal_name: str) -> NewUsersVisitReadSchema:
       ...

    async def get_or_create(self: Self, create_object: NewUsersVisitCreateSchema) -> tuple[NewUsersVisitReadSchema, bool]:
        ...

    async def get_by_ip(self: Self, user_visit_id: uuid.UUID, ip_address: str) -> NewUsersVisitReadSchema:
        ...

class NewUsersVisitRepository(NewUsersVisitRepositoryProtocol):
    async def register(self: Self, visit_id: uuid.UUID, character_id: uuid.UUID, refferal_name: str) -> NewUsersVisitReadSchema:
        async with self.session as session, session.begin():
            query = (
                sa.update(self.model_type)
                .where(self.model_type.id == visit_id)
                .values(
                    character_id=character_id,
                    is_registered=True,
                    refferal_name=refferal_name
                )
                .returning(self.model_type)
            )
            result = await session.execute(query)
            updated_visit = result.scalar_one_or_none()
            if not updated_visit:
                raise ModelNotFoundException(self.model_type, visit_id)
            return self.read_schema_type.model_validate(updated_visit, from_attributes=True)
    
    async def get_or_create(
        self: Self, 
        create_object: NewUsersVisitCreateSchema
    ) -> tuple[NewUsersVisitReadSchema, bool]:
        """
        Получить существующий визит по IP или создать новый.
        
        Args:
            create_object: Данные для создания визита
        
        Returns:
            tuple: (объект визита, created) где created=True если визит был создан
        """
        async with self.session as session, session.begin():
            # Пытаемся найти существующую запись по IP
            stmt_select = (
                sa.select(self.model_type).where(
                    self.model_type.ip_address == create_object.ip_address
                )
                .order_by(self.model_type.created_at)
                .limit(1)

            )
            result = await session.execute(stmt_select)
            existing_visit = result.scalar_one_or_none()
            
            if existing_visit:
                # Визит с таким IP уже существует
                return (
                    self.read_schema_type.model_validate(existing_visit, from_attributes=True),
                    False
                )
            
            # Визита нет, создаём новый
            try:
                stmt_insert = (
                    sa.insert(self.model_type)
                    .values(**create_object.model_dump(exclude={'id'}))
                    .returning(self.model_type)
                )
                new_visit = (await session.execute(stmt_insert)).scalar_one()
                return (
                    self.read_schema_type.model_validate(new_visit, from_attributes=True),
                    True
                )
            except IntegrityError:
                # Race condition: запись была создана между SELECT и INSERT
                await session.rollback()
                
                # Получаем созданную другим процессом запись
                result = await session.execute(stmt_select)
                existing_visit = result.scalar_one()
                return (
                    self.read_schema_type.model_validate(existing_visit, from_attributes=True),
                    False
                )

    async def get_by_ip(self: Self, user_visit_id: uuid.UUID, ip_address: str) -> NewUsersVisitReadSchema:
        async with self.session as session, session.begin():
            query = (
                sa.select(self.model_type)
                .where(self.model_type.ip_address == ip_address,
                       self.model_type.id == user_visit_id)
            )
            result = await session.execute(query)
            visit = result.scalar_one_or_none()
            if not visit:
                raise ModelNotFoundException(self.model_type, ip_address)
            return self.read_schema_type.model_validate(visit, from_attributes=True)