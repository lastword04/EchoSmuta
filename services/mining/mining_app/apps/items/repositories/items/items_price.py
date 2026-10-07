from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import ItemPrice
from ...schemas import ItemPriceCreateSchema, ItemPriceReadSchema, ItemPriceUpdateSchema


class ItemPriceRepositoryProtocol(
    BaseRepositoryImpl[
        ItemPrice,
        ItemPriceReadSchema,
        ItemPriceCreateSchema,
        ItemPriceUpdateSchema
    ]
):
    pass

class ItemPriceRepository(ItemPriceRepositoryProtocol):
    pass