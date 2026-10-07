from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.chat import ChatSettingsReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.settings import ChatSettingsServiceProtocol


class GetMeChatSettingsUseCaseProtocol(UseCaseProtocol[ChatSettingsReadSchema]):
    async def __call__(self, token: UserTokenDataReadSchema) -> ChatSettingsReadSchema:
        ...


class GetMeChatSettingsUseCase(GetMeChatSettingsUseCaseProtocol):
    def __init__(self, chat_settings_service: ChatSettingsServiceProtocol):
        self.chat_settings_service = chat_settings_service

    async def __call__(self, token: UserTokenDataReadSchema) -> ChatSettingsReadSchema:
        return await self.chat_settings_service.get_by_character_id(token.character_id)