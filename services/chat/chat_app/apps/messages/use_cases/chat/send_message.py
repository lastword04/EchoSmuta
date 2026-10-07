from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.messages import MessageServiceProtocol
from ...schemas import MessageRequestSchema, MessageReadSchema


class SendMessageUseCaseProtocol(UseCaseProtocol[MessageReadSchema]):
    async def __call__(self, room: str, message: MessageRequestSchema, user_data: UserTokenDataReadSchema) -> MessageReadSchema:
        ...

class SendMessageUseCase(SendMessageUseCaseProtocol):
    def __init__(self,
                 message_service: MessageServiceProtocol):
        self.message_service = message_service

    async def __call__(self, room: str, message: MessageRequestSchema, user_data: UserTokenDataReadSchema) -> MessageReadSchema:
        return await self.message_service.create_message(
            room=room,
            message=message,
            character_id=user_data.character_id,
        )