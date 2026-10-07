from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import GlobalCharacterSettings
from ...schemas import GlobalCharacterSettingsReadSchema, GlobalCharacterSettingsCreateSchema, GlobalCharacterSettingsUpdateDBSchema


class GlobalCharacterSettingsRepositoryProtocol(BaseRepositoryImpl[
    GlobalCharacterSettings,
    GlobalCharacterSettingsReadSchema,
    GlobalCharacterSettingsCreateSchema,
    GlobalCharacterSettingsUpdateDBSchema
]):
    pass
    


class GlobalCharacterSettingsRepository(GlobalCharacterSettingsRepositoryProtocol):
    pass
