import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelNotFoundException
from ...models import Building


class BuildingSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model_type = Building

    def get_by_city_trading_location(self, city_trading_location_slug: str) -> Building:
        """Получить здание по city_trading_location_slug"""
        stmt = sa.select(self.model_type).where(
            self.model_type.city_trading_location_slug == city_trading_location_slug
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ModelNotFoundException(self.model_type, city_trading_location_slug)
        return model

    def get_by_location_slug(self, location_slug: str) -> Building | None:
        """Получить здание по location_slug"""
        stmt = sa.select(self.model_type).where(
            self.model_type.location_slug == location_slug
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()