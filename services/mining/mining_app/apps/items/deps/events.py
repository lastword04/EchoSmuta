"""Провайдеры публикаторов событий items / deals.

Общий инфраструктурный слой: используется доменами recipes, deals, crafting,
character, shop, sale, purchase, items.
"""
from fastapi import Depends

from ...resources.depends import get_redis_publisher
from ...resources.events.publisher import RedisPublisherProtocol
from ..events.deals import DealEvents, DealEventsProtocol
from ..events.items import ItemEvents, ItemEventsProtocol


def get_items_events(
    publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> ItemEventsProtocol:
    return ItemEvents(publisher)


def get_deal_events(
    publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
) -> DealEventsProtocol:
    return DealEvents(publisher)

