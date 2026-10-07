import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import CityTradingShopSettings
from ...schemas import (
    CityTradingShopSettingsCreateSchema,
    CityTradingShopSettingsReadSchema,
    CityTradingShopSettingsUpdateSchema,
)


class CityTradingShopSettingsRepositoryProtocol(
    BaseRepositoryImpl[
        CityTradingShopSettings,
        CityTradingShopSettingsReadSchema,
        CityTradingShopSettingsCreateSchema,
        CityTradingShopSettingsUpdateSchema
    ]
):
    async def get_by_location_and_level(self, location_slug: str, level: int) -> CityTradingShopSettingsReadSchema:
        ...

class CityTradingShopSettingsRepository(CityTradingShopSettingsRepositoryProtocol):
    async def get_by_location_and_level(self, location_slug: str, level: int) -> CityTradingShopSettingsReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.location_slug == location_slug,
                       self.model_type.level == level)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "location_slug", location_slug)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)