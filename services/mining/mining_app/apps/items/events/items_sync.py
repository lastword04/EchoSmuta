import asyncio

from shared.schemas.item_events import ItemMessageEventSchema


class ItemEventsSyncAdapter:
    def __init__(self, async_adapter):
        self.async_adapter = async_adapter

    def publish_message(self, event: ItemMessageEventSchema) -> None:
        asyncio.run(self.async_adapter.publish_message(event))