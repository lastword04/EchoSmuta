import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelFieldNotFoundException
from ...models import Item
from ...schemas import ItemReadSchema


class ItemSyncRepository:
    def __init__(self, session: Session):
        self.session = session
        self.model_type = Item

    def get_by_slug(self, slug: str) -> ItemReadSchema:
        stmt = sa.select(self.model_type).where(self.model_type.slug == slug)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ModelFieldNotFoundException(self.model_type, "slug", slug)
        return ItemReadSchema.model_validate(model, from_attributes=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()