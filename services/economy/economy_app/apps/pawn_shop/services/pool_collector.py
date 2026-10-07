import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.clients.mining_client import MiningClient
from ..models import BuyoutStock, PoolSnapshot, PoolType, Resource


class PoolCollectorService:
    def __init__(self, mining_client: MiningClient) -> None:
        self.mining_client = mining_client

    async def get_buyout_quantities(self, session: AsyncSession) -> dict[uuid.UUID, Decimal]:
        rows = await session.execute(select(BuyoutStock.resource_id, BuyoutStock.quantity))
        return {resource_id: Decimal(str(quantity)) for resource_id, quantity in rows.all()}

    async def get_location_quantities(self, resources: list[Resource]) -> dict[str, Decimal]:
        payload = await self.mining_client.get_locations()
        return self._parse_resource_amounts(payload)

    async def get_player_quantities(self) -> dict[str, Decimal]:
        data = await self.mining_client.get_players_resources()
        return {item["resource_slug"]: Decimal(item["amount"]) for item in data}

    @staticmethod
    def _parse_resource_amounts(payload: object) -> dict[str, Decimal]:
        if isinstance(payload, dict):
            items = payload.get("resources", payload.get("items", []))
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

        result: dict[str, Decimal] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            slug = item.get("resource_slug") or item.get("code") or item.get("slug")
            amount = item.get("amount", item.get("quantity", item.get("current_amount", 0)))
            if slug is not None:
                key = str(slug)
                result[key] = result.get(key, Decimal("0")) + Decimal(str(amount))
        return result
