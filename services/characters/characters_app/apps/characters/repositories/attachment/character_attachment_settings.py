from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import CharacterAttachmentSettings
from ...schemas import CharacterAttachmentSettingsCreateSchema, CharacterAttachmentSettingsUpdateDBSchema, CharacterAttachmentSettingsReadSchema


class CharacterAttachmentSettingsRepositoryProtocol(BaseRepositoryImpl[
    CharacterAttachmentSettings,
    CharacterAttachmentSettingsReadSchema,
    CharacterAttachmentSettingsCreateSchema,
    CharacterAttachmentSettingsUpdateDBSchema
]):
    pass
    


class CharacterAttachmentSettingsRepository(CharacterAttachmentSettingsRepositoryProtocol):
    pass
