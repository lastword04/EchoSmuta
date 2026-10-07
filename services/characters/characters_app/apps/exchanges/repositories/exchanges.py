from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import ExchangeSettings
from ..schemas import ExchangeSettingsCreateSchema, ExchangeSettingsUpdateDBSchema, ExchangeSettingsReadSchema

class ExchangeSettingsRepositoryProtocol(
    BaseRepositoryImpl[
        ExchangeSettings, 
        ExchangeSettingsReadSchema, 
        ExchangeSettingsCreateSchema, 
        ExchangeSettingsUpdateDBSchema
    ]
):
    pass

class ExchangeSettingsRepository(ExchangeSettingsRepositoryProtocol):
    pass