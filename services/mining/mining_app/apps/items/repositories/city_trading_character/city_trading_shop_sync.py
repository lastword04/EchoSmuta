import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelNotFoundException
from ...models import CityTradingShop


class CityTradingShopSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model_type = CityTradingShop

    def get_by_location_and_character(self, location_slug: str, character_id: uuid.UUID) -> CityTradingShop | None:
        stmt = sa.select(self.model_type).where(
            self.model_type.location_slug == location_slug,
            self.model_type.character_id == character_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, shop_id: uuid.UUID) -> CityTradingShop:
        model = self.session.get(self.model_type, shop_id)
        if model is None:
            raise ModelNotFoundException(self.model_type, shop_id)
        return model

    def update_current_capacity(self, shop_id: uuid.UUID, additional_capacity: int) -> None:
        stmt = (
            sa.update(self.model_type)
            .where(self.model_type.id == shop_id)
            .values(current_capacity=self.model_type.current_capacity + additional_capacity)
        )
        self.session.execute(stmt)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()