import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.block_characters import CheckSendMailRepositoryProtocol


class CheckSendMailServiceProtocol(Protocol):
    async def can_send_message(
        self: Self,
        sender_character_id: uuid.UUID,
        recipient_character_id: uuid.UUID
    ) -> bool:
        ...

class CheckSendMailService(CheckSendMailServiceProtocol):
    def __init__(self: Self, repository: CheckSendMailRepositoryProtocol):
        self.repository = repository

    async def can_send_message(
        self: Self,
        sender_character_id: uuid.UUID,
        recipient_character_id: uuid.UUID
    ) -> bool:
        return await self.repository.can_send_message(sender_character_id, recipient_character_id)
    