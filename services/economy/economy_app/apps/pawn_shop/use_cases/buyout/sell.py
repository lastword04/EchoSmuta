import uuid
from decimal import Decimal
from typing import Any
import logging

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...models import BuyoutStock, EconomyTransaction, TransactionType
from ...schemas import TradeRequest
from ...service import get_price, get_resource
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

logger = logging.getLogger(__name__)


class SellResourceToBuyoutUseCase:
    def __init__(self, characters_client: CharactersClient, mining_client: MiningClient, 
                economy_events: EconomyEventsProtocol, template_service: EconomyTemplateServiceProtocol) -> None:
        self.characters_client = characters_client
        self.mining_client = mining_client
        self.economy_events = economy_events
        self.template_service = template_service

    async def __call__(self, data: TradeRequest, character_id: uuid.UUID, session: AsyncSession) -> dict[str, Any]:
        resource = await get_resource(session, data.resource_id)
        price = await get_price(session, resource.id)
        stock = await session.scalar(select(BuyoutStock).where(BuyoutStock.resource_id == resource.id).with_for_update())
        if stock is None:
            stock = BuyoutStock(resource_id=resource.id, quantity=0)
            session.add(stock)

        resource_amount = data.quantity
        total_price = (data.quantity * price.buy_price).quantize(Decimal("0.01"))

        await self._ensure_player_has_resource(resource.code, character_id, resource_amount)

        operation_id = uuid.uuid4()
        op_debit = uuid.uuid5(operation_id, "debit")
        op_credit = uuid.uuid5(operation_id, "credit")
        op_refund = uuid.uuid5(operation_id, "debit-refund")
        debited = False
        try:
            await self.mining_client.debit(resource.code, character_id, resource_amount, op_debit)
            debited = True
            await self.characters_client.credit(
                character_id, total_price,
                operation_id=op_credit,
                operation_type="buyout_sale",
                source="economy.buyout",
                item_meta={
                    "resource_code": resource.code,
                    "resource_id": str(resource.id),
                    "amount": resource_amount,
                },
            )
        except httpx.HTTPStatusError as exc:
            if debited:
                try:
                    await self.mining_client.credit(resource.code, character_id, resource_amount, op_refund)
                except Exception as re:
                    logger.error("Refund failed after characters.credit error: %s", re)
            if exc.response.status_code == 409:
                raise HTTPException(status_code=409, detail="External service rejected buyout sell operation") from exc
            raise HTTPException(status_code=502, detail="External service error") from exc
        except httpx.HTTPError as exc:
            if debited:
                try:
                    await self.mining_client.credit(resource.code, character_id, resource_amount, op_refund)
                except Exception as re:
                    logger.error("Refund failed after characters.credit error: %s", re)
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        stock.quantity += resource_amount
        transaction = EconomyTransaction(
            transaction_type=TransactionType.BUYOUT_SELL,
            resource_id=resource.id,
            quantity=data.quantity,
            price_per_unit=price.buy_price,
            total=total_price,
            buyer_id=None,
            seller_id=character_id,
            lot_id=None,
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        # Получаем локацию персонажа для события
        try:
            location_slug = await self.characters_client.get_character_location(character_id)
        except Exception as e:
            logger.warning(f"Failed to get character location: {e}")
            location_slug = "unknown"

        # Публикуем событие в чат
        try:
            items_list = f"{data.quantity} {self.template_service._plural_briquet(data.quantity)} ресурса {resource.name}"
            message_text = self.template_service.get_buyout_sell_message(
                items_list=items_list,
                price=str(total_price),
            )
            await self.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type="economy_buyout_sell",
                    character_id=character_id,
                    location_slug=location_slug,
                    content=message_text,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_sell event: {e}")

        try:
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "buyout_stock_updated",
                    "location_slug": location_slug,
                    "initiator_character_id": str(character_id),
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_stock_updated: {e}")

        return {
            "transaction_id": transaction.id,
            "resource_id": resource.id,
            "quantity": data.quantity,
            "price_per_unit": price.buy_price,
            "total_price": total_price,
            "operation_id": operation_id,
        }

    async def _ensure_player_has_resource(self, resource_code: str, character_id: uuid.UUID, required_amount: int) -> None:
        try:
            payload = await self.mining_client.get_player_resources(character_id)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        resources = payload.get("resources", payload if isinstance(payload, list) else [])
        current_amount = 0
        for item in resources:
            if item.get("resource_slug") == resource_code:
                current_amount = int(item.get("amount", 0))
                break
        if current_amount < required_amount:
            raise HTTPException(status_code=409, detail=f"Недостаточно ресурса для продажи.")