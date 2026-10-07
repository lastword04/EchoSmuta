import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelFieldNotFoundException
from ...enums import ItemType
from ...models import Item
from ...schemas import ItemCreateSchema, ItemReadSchema, ItemUpdateSchema


class ItemRepositoryProtocol(
    BaseRepositoryImpl[
        Item,
        ItemReadSchema,
        ItemCreateSchema,
        ItemUpdateSchema
    ]
):
    async def get_by_slug(self, slug: str) -> ItemReadSchema:
        ...

    async def bulk_update(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        ...

class ItemRepository(ItemRepositoryProtocol):
    async def get_by_slug(self, slug: str) -> ItemReadSchema:
        async with self.session as s:
            stmt = sa.select(self.model_type).where(self.model_type.slug == slug)
            result = await s.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model is None:
                raise ModelFieldNotFoundException(self.model_type, "slug", slug)
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def bulk_update(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        async with self.session as s:
            slugs = [item.slug for item in items]
            stmt = sa.select(self.model_type).where(self.model_type.slug.in_(slugs))
            result = await s.execute(stmt)
            existing_models = {model.slug: model for model in result.scalars().all()}

            updated = []
            for item_schema in items:
                model = existing_models.get(item_schema.slug)
                if model is not None:
                    update_data = item_schema.model_dump(exclude_unset=True)

                    # Приводим item_type к Enum-объекту: SQLAlchemy запишет ИМЯ ('KIT'),
                    # как исторически хранится в этой базе
                    if 'item_type' in update_data:
                        val = update_data['item_type']
                        if not isinstance(val, ItemType):
                            try:
                                val = ItemType(val)    # строка 'kit'
                            except ValueError:
                                val = ItemType[val]    # строка 'KIT'
                        update_data['item_type'] = val

                    for key, value in update_data.items():
                        setattr(model, key, value)
                    updated.append(model)

            # Схемы строим ДО commit: после commit SQLAlchemy помечает объекты
            # expired, и обращение к их атрибутам даёт по одному
            # SELECT items ... WHERE id (N+1). Значения уже загружены селектом выше —
            # читаем их из памяти, не трогая модели после commit.
            result = [
                self.read_schema_type.model_validate(m, from_attributes=True)
                for m in updated
            ]
            await s.commit()
            return result