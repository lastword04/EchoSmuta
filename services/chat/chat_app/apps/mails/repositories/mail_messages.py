import uuid
from typing import Optional, Iterable, Any
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException, ModelAlreadyExistsError
from ..models import MailMessage
from ..schemas import (
    MailMessageReadSchema,
    MailMessageCreateSchema,
    MailMessageUpdateSchema,
    MailMessagePaginationResultSchema
)

class MailMessageRepositoryProtocol(BaseRepositoryImpl[
    MailMessage,
    MailMessageReadSchema,
    MailMessageCreateSchema,
    MailMessageUpdateSchema,
]):
    async def update_activity_sender_message(self: Self, mail_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        ...

    async def update_activity_recipient_message(self: Self, mail_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        ...

    async def paginate_by_character_and_visibility(
        self: Self,
        pagination: PaginationSchema,
        sorting: Iterable[str],
        user: Any,
        policies: list[str],
        from_character_id: Optional[uuid.UUID] = None,
        to_character_id: Optional[uuid.UUID] = None,
    ) -> MailMessagePaginationResultSchema:
        ...

    async def update_all_messages_to_is_read(self: Self, character_id: uuid.UUID) -> bool:
        ...

    async def check_not_is_read_messages(self: Self, character_id: uuid.UUID) -> bool:
        ...

class MailMessageRepository(MailMessageRepositoryProtocol):
    async def update_activity_sender_message(self: Self, mail_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        async with self.session as s, s.begin():
            statement = (
                sa.update(self.model_type)
                .where(
                    self.model_type.id == mail_id,
                    self.model_type.from_character_id == character_id
                )
                .values(is_active_sender=False)
            )

            result = await s.execute(statement)
            if result.rowcount == 0:
                raise ModelNotFoundException(MailMessage, mail_id)
            
            return True


    async def update_activity_recipient_message(self: Self, mail_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        async with self.session as s, s.begin():
            statement = (
                sa.update(self.model_type)
                .where(
                    self.model_type.id == mail_id,
                    self.model_type.to_character_id == character_id
                )
                .values(is_active_recipient=False)
            )

            result = await s.execute(statement)
            if result.rowcount == 0:
                raise ModelNotFoundException(MailMessage, mail_id)
            
            return True
    

    async def paginate_by_character_and_visibility(
        self: Self,
        pagination: PaginationSchema,
        sorting: Iterable[str],
        user: Any,
        policies: list[str],
        from_character_id: Optional[uuid.UUID] = None,
        to_character_id: Optional[uuid.UUID] = None,
    ) -> MailMessagePaginationResultSchema:
        if len(policies) == 0:
            return MailMessagePaginationResultSchema(objects=[], count=0)

        if from_character_id and to_character_id:
            raise ValueError("Cannot filter by both from_character_id and to_character_id at the same time.")

        if not from_character_id and not to_character_id:
            raise ValueError("Either from_character_id or to_character_id must be provided.")

        async with self.session as s:
            statement = sa.select(self.model_type)

            if from_character_id:
                statement = statement.where(self.model_type.from_character_id == from_character_id,
                                            self.model_type.is_active_sender == True)
            elif to_character_id:
                statement = statement.where(self.model_type.to_character_id == to_character_id,
                                            self.model_type.is_active_recipient == True)

            order_by_expr = self.get_order_by_expr(sorting)

            models = (
                (await s.execute(
                    statement
                    .limit(pagination.limit)
                    .offset(pagination.offset)
                    .order_by(*order_by_expr)
                ))
                .scalars()
                .all()
            )

            objects = [
                self.read_schema_type.model_validate(model, from_attributes=True)
                for model in models
            ]

            count_statement = statement.with_only_columns(sa.func.count(self.model_type.id))
            count = (await s.execute(count_statement)).scalar_one()

            return MailMessagePaginationResultSchema(count=count, objects=objects)
        
    async def update_all_messages_to_is_read(self: Self, character_id: uuid.UUID) -> bool:
        try:
            async with self.session as s, s.begin():
                stmt = (
                    sa.update(self.model_type)
                    .where(self.model_type.to_character_id == character_id)
                    .values(is_read=True)
                )

                await s.execute(stmt)

                return True
        except IntegrityError as e:
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                raise ModelAlreadyExistsError(self.model_type, "character_id", "duplicate key")

            raise
    
    async def check_not_is_read_messages(self: Self, character_id: uuid.UUID) -> bool:
        async with self.session as s:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.to_character_id == character_id,
                    self.model_type.is_read == False
                )
                .limit(1)
            )
            
            result = await s.execute(stmt)
            has_unread = result.first()
            
            return has_unread is None
