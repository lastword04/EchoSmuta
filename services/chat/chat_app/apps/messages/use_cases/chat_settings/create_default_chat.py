from shared.schemas.chat import ChatSettingsDefaultCreateSchema, ChatSettingsReadSchema
from ....categories.use_cases.categories.create_default import CreateDefaultCategoriesUseCaseProtocol
from ..chat.send_default_messages import SendDefaultMessagesUseCaseProtocol
from .create_default import CreateDefaultSettingsUseCaseProtocol


class CreateDefaultChatUseCase(CreateDefaultSettingsUseCaseProtocol):
    def __init__(self, chat_settings_use_case: CreateDefaultSettingsUseCaseProtocol,
                 categories_use_case: CreateDefaultCategoriesUseCaseProtocol,
                 messages_use_case: SendDefaultMessagesUseCaseProtocol):
        self.chat_settings_use_case = chat_settings_use_case
        self.categories_use_case = categories_use_case
        self.messages_use_case = messages_use_case

    async def __call__(self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        await self.messages_use_case(data.character_id, data.character_name, data.is_main)
        await self.categories_use_case(data.character_id)
        return await self.chat_settings_use_case(data)
