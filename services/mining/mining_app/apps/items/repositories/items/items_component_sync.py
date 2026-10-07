import sqlalchemy as sa
from sqlalchemy.orm import Session

from ....resources.models import Resource
from ...models import ItemComponent
from ...schemas import ItemComponentWithResourceSchema


class ItemComponentSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_components_with_resource_names(self, item_slug: str) -> list[ItemComponentWithResourceSchema]:
        stmt = (
            sa.select(
                ItemComponent.id,
                ItemComponent.item_slug,
                ItemComponent.resource_slug,
                ItemComponent.quantity,
                Resource.name.label('resource_name')
            )
            .join(Resource, ItemComponent.resource_slug == Resource.slug)
            .where(ItemComponent.item_slug == item_slug)
        )
        rows = self.session.execute(stmt).all()
        return [
            ItemComponentWithResourceSchema(
                id=row.id,
                item_slug=row.item_slug,
                resource_slug=row.resource_slug,
                quantity=row.quantity,
                resource_name=row.resource_name
            )
            for row in rows
        ]

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()