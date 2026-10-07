import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.chat import ChatSettingsReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.settings import ChatSettingsServiceProtocol
from ...schemas import ChatSettingsUpdateSchema
from ..valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol

class UpdateChatSettingsUseCaseProtocol(UseCaseProtocol[ChatSettingsReadSchema]):
    async def __call__(self, settings_id: uuid.UUID, settings: ChatSettingsUpdateSchema, token: UserTokenDataReadSchema) -> ChatSettingsReadSchema:
        ...

class UpdateChatSettingsUseCase(UpdateChatSettingsUseCaseProtocol):
    def __init__(self, chat_settings_service: ChatSettingsServiceProtocol,
                 valid_or_raise: GetIsOnlineCharacterOrRaiseUseCaseProtocol):
        self.chat_settings_service = chat_settings_service
        self.valid_or_raise = valid_or_raise

    async def __call__(self, settings_id: uuid.UUID, settings: ChatSettingsUpdateSchema, token: UserTokenDataReadSchema) -> ChatSettingsReadSchema:
        await self.valid_or_raise(token)
        return await self.chat_settings_service.update(token.character_id, settings_id, settings)