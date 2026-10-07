import uuid
from typing import Protocol
from typing_extensions import Self
import sqlalchemy as sa
from ..models import Category, CategoryCharacter
from ....core.db import AsyncSession

class CheckSendMailRepositoryProtocol(Protocol):
    async def can_send_message(
        self: Self,
        sender_character_id: uuid.UUID,
        recipient_character_id: uuid.UUID
    ) -> bool:
        ...

class CheckSendMailRepository(CheckSendMailRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_send_message(
        self: Self,
        sender_character_id: uuid.UUID,
        recipient_character_id: uuid.UUID
    ) -> bool:
        """
        Проверяет, может ли отправитель написать получателю.
        Возвращает True, если может написать, False если заблокирован.
        """
        async with self.session as s:
            # Проверяем, есть ли sender_character_id в категории получателя
            # с установленным флагом is_block_send_mails = True
            statement = (
                sa.select(sa.func.count())
                .select_from(CategoryCharacter)
                .join(
                    Category,
                    CategoryCharacter.category_id == Category.id
                )
                .where(
                    Category.owner_character_id == recipient_character_id,
                    CategoryCharacter.character_id == sender_character_id,
                    Category.is_block_send_mails == True
                )
            )
            
            result = await s.execute(statement)
            blocked_count = result.scalar()
            
            return blocked_count == 0