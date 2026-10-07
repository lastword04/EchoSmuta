from typing_extensions import Self
from ...schemas import CharacterAttachmentSettingsReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.attachment.character_attachment_service import CharacterAttachmentSettingsServiceProtocol 


class GetCharacterAttachmentSettingsUseCaseProtocol(UseCaseProtocol[CharacterAttachmentSettingsReadSchema]):
    async def __call__(self: Self) -> CharacterAttachmentSettingsReadSchema:
        ...


class GetCharacterAttachmentSettingsUseCase(GetCharacterAttachmentSettingsUseCaseProtocol):
    def __init__(self: Self, service: CharacterAttachmentSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> CharacterAttachmentSettingsReadSchema:
        return (await self.service.get_all())[0]
