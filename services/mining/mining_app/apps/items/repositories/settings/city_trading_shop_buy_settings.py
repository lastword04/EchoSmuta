import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import CityTradingShopBuySettings
from ...schemas import (
    CityTradingShopBuySettingsCreateSchema,
    CityTradingShopBuySettingsReadSchema,
    CityTradingShopBuySettingsUpdateSchema,
)


class CityTradingShopBuySettingsRepositoryProtocol(
    BaseRepositoryImpl[
        CityTradingShopBuySettings,
        CityTradingShopBuySettingsReadSchema,
        CityTradingShopBuySettingsCreateSchema,
        CityTradingShopBuySettingsUpdateSchema
    ]
):
    async def get_by_location_slug(self, location_slug: str) -> CityTradingShopBuySettingsReadSchema:
        ...

class CityTradingShopBuySettingsRepository(CityTradingShopBuySettingsRepositoryProtocol):
    async def get_by_location_slug(self, location_slug: str) -> CityTradingShopBuySettingsReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.location_slug == location_slug)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "location_slug", location_slug)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)