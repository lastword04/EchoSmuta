from shared.schemas.chat import ChatSettingsDefaultCreateSchema, ChatSettingsReadSchema
from .....core.use_cases import UseCaseProtocol
from ...services.settings import ChatSettingsServiceProtocol

class CreateDefaultSettingsUseCaseProtocol(UseCaseProtocol[ChatSettingsReadSchema]):
    async def __call__(self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        ...

class CreateDefaultSettingsUseCase(CreateDefaultSettingsUseCaseProtocol):
    def __init__(self, service: ChatSettingsServiceProtocol):
        self.service = service

    async def __call__(self, data: ChatSettingsDefaultCreateSchema) -> ChatSettingsReadSchema:
        return await self.service.create_default(data)