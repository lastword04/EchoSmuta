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


class BuyResourceFromBuyoutUseCase:
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
        if stock is None or stock.quantity < data.quantity:
            raise HTTPException(status_code=409, detail="Этого ресурса уже нет в скупке")

        resource_amount = data.quantity
        total_price = (data.quantity * price.sell_price).quantize(Decimal("0.01"))
        balance = await self.characters_client.get_balance(character_id)
        if balance < total_price:
            raise HTTPException(status_code=409, detail=f"Недостаточно дукатов.")

        operation_id = uuid.uuid4()
        op_debit = uuid.uuid5(operation_id, "debit")
        op_credit = uuid.uuid5(operation_id, "credit")
        op_refund = uuid.uuid5(operation_id, "debit-refund")
        debited = False
        try:
            await self.characters_client.debit(
                character_id, total_price,
                operation_id=op_debit,
                operation_type="buyout_purchase",
                source="economy.buyout",
                item_meta={"resource_code": resource.code, "resource_id": str(resource.id)},
            )
            debited = True
            await self.mining_client.credit(resource.code, character_id, resource_amount, op_credit)
        except httpx.HTTPStatusError as exc:
            if debited:
                try:
                    await self.characters_client.credit(
                        character_id, total_price,
                        operation_id=op_refund,
                        operation_type="buyout_purchase_refund",
                        source="economy.buyout",
                        item_meta={"compensates": str(op_debit)},
                    )
                except Exception as re:
                    logger.error("Refund failed after mining.credit error: %s", re)
            if exc.response.status_code == 409:
                raise HTTPException(status_code=409, detail="External service rejected buyout buy operation") from exc
            raise HTTPException(status_code=502, detail="External service error") from exc
        except httpx.HTTPError as exc:
            if debited:
                try:
                    await self.characters_client.credit(
                        character_id, total_price,
                        operation_id=op_refund,
                        operation_type="buyout_purchase_refund",
                        source="economy.buyout",
                        item_meta={"compensates": str(op_debit)},
                    )
                except Exception as re:
                    logger.error("Refund failed after mining.credit error: %s", re)
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        stock.quantity -= resource_amount
        transaction = EconomyTransaction(
            transaction_type=TransactionType.BUYOUT_BUY,
            resource_id=resource.id,
            quantity=data.quantity,
            price_per_unit=price.sell_price,
            total=total_price,
            buyer_id=character_id,
            seller_id=None,
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
            message_text = self.template_service.get_buyout_buy_message(
                items_list=items_list,
                price=str(total_price),
            )
            await self.economy_events.publish_message(
                ItemMessageEventSchema(
                    event_type="economy_buyout_buy",
                    character_id=character_id,
                    location_slug=location_slug,
                    content=message_text,
                    scope=ItemMessageScope.PRIVATE,
                    target_user_ids=[character_id],
                )
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_buy event: {e}")

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
            "price_per_unit": price.sell_price,
            "total_price": total_price,
            "operation_id": operation_id,
        }