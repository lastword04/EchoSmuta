import uuid
from typing import Optional
from .....core.use_cases import UseCaseProtocol
from ...services.messages import MessageServiceProtocol
from ...schemas import MessageReadSchema, MessageRequestSchema
from ...enums import MessageType

class SendSystemMessageUseCaseProtocol(UseCaseProtocol[MessageReadSchema]):
    async def __call__(self, room: str, content: str, message_type: Optional[MessageType], 
                       is_trade: bool = False,
                       target_user_ids: Optional[list[uuid.UUID]] = None,
                       character_id: Optional[list[uuid.UUID]] = None) -> MessageReadSchema:
        ...

class SendSystemMessageUseCase(SendSystemMessageUseCaseProtocol):
    def __init__(self,
                 message_service: MessageServiceProtocol):
        self.message_service = message_service

    async def __call__(self, room: str, content: str, message_type: Optional[MessageType], 
                       is_trade: bool = False,
                       target_user_ids: Optional[list[uuid.UUID]] = None,
                       character_id: Optional[list[uuid.UUID]] = None) -> MessageReadSchema:
        message_request = MessageRequestSchema(content=content, 
                                               target_user_ids=target_user_ids,
                                               is_trade=is_trade
        )

        return await self.message_service.create_message_direct(
            message_type=message_type,
            room=room,
            message=message_request,
            character_id=character_id
        )