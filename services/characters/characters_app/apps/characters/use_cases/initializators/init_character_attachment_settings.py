from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import CharacterAttachmentSettingsCreateSchema, CharacterAttachmentSettingsReadSchema
from ...services.attachment.character_attachment_service import CharacterAttachmentSettingsServiceProtocol 


class InitializeCharacterAttachmentSettingsUseCaseProtocol(UseCaseProtocol[CharacterAttachmentSettingsReadSchema]):
    async def __call__(self: Self) -> CharacterAttachmentSettingsReadSchema:
        ...


class InitializeCharacterAttachmentSettingsUseCase(InitializeCharacterAttachmentSettingsUseCaseProtocol):
    def __init__(self: Self, service: CharacterAttachmentSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> CharacterAttachmentSettingsReadSchema:

        attachment_settings = await self.service.get_all()

        if len(attachment_settings) > 0:
            return attachment_settings

        default_attachment_settings = self._get_default_attachment_settings()
        return await self.service.create(default_attachment_settings)

    def _get_default_attachment_settings(self: Self) -> CharacterAttachmentSettingsReadSchema:
        return CharacterAttachmentSettingsCreateSchema(
            attach_cost=settings.character_attachment_settings.attach_cost,
            detach_cost=settings.character_attachment_settings.detach_cost,
            attach_cost_per_level=settings.character_attachment_settings.attach_cost_per_level,
            detach_cost_per_level=settings.character_attachment_settings.detach_cost_per_level
        )