from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import TransferValueCharactersSettings
from ...schemas import TransferValueCharactersSettingsReadSchema, TransferValueCharactersSettingsCreateSchema, TransferValueCharactersSettingsUpdateDBSchema


class TransferValueCharactersSettingsRepositoryProtocol(BaseRepositoryImpl[
    TransferValueCharactersSettings,
    TransferValueCharactersSettingsReadSchema,
    TransferValueCharactersSettingsCreateSchema,
    TransferValueCharactersSettingsUpdateDBSchema
]):
    pass
    


class TransferValueCharactersSettingsRepository(TransferValueCharactersSettingsRepositoryProtocol):
    pass
