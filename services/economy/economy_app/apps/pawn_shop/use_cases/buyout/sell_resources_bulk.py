import uuid
from typing import Any
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from fastapi import HTTPException
import logging

from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...models import BuyoutStock, EconomyTransaction, TransactionType
from ...schemas import BulkTradeRequest, TradeRequest
from ...service import get_price, get_resource
from ...events.economy import EconomyEventsProtocol
from ...services.economy_templates import EconomyTemplateServiceProtocol
from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope
from shared.utils.plural import plural
from .sell import SellResourceToBuyoutUseCase

logger = logging.getLogger(__name__)


class SellResourcesBulkUseCase:
    def __init__(self, sell_use_case: SellResourceToBuyoutUseCase) -> None:
        self.sell_use_case = sell_use_case

    async def __call__(
        self, 
        data: BulkTradeRequest, 
        character_id: uuid.UUID, 
        session: AsyncSession
    ) -> list[dict[str, Any]]:
        """Продаёт несколько ресурсов одним запросом с ОДНИМ сообщением."""
        results = []
        total_price = Decimal("0")
        resources_parts = []
        
        # Проверяем наличие ресурсов
        try:
            payload = await self.sell_use_case.mining_client.get_player_resources(character_id)
            resources_payload = payload.get("resources", payload if isinstance(payload, list) else [])
            player_resources = {r.get("resource_slug"): int(r.get("amount", 0)) for r in resources_payload}
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc
        
        # Склеиваем дубликаты: суммируем количества по каждому ресурсу
        aggregated: dict[uuid.UUID, int] = {}
        for item in data.items:
            if item.quantity <= 0:
                raise HTTPException(status_code=422, detail="Количество должно быть больше нуля")
            aggregated[item.resource_id] = aggregated.get(item.resource_id, 0) + item.quantity

        debited_ops: list[tuple[str, int, uuid.UUID, Decimal]] = []  # (code, qty, op_debit, price)
        for resource_id, quantity in aggregated.items():
            resource = await get_resource(session, resource_id)
            price = await get_price(session, resource.id)

            current_amount = player_resources.get(resource.code, 0)
            if current_amount < quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Недостаточно ресурса {resource.name}. Требуется: {quantity}, доступно: {current_amount}"
                )

            item_total_price = (quantity * price.buy_price).quantize(Decimal("0.01"))
            total_price += item_total_price
            resources_parts.append(f"{quantity} {plural(quantity, 'брикет', 'брикета', 'брикетов')} ресурса {resource.name}")

            op_debit = uuid.uuid5(uuid.uuid4(), "debit")
            op_credit = uuid.uuid5(op_debit, "credit")
            op_refund = uuid.uuid5(op_debit, "debit-refund")
            try:
                await self.sell_use_case.mining_client.debit(resource.code, character_id, quantity, op_debit)
                debited_ops.append((resource.code, quantity, op_debit, item_total_price))
                await self.sell_use_case.characters_client.credit(
                    character_id, item_total_price,
                    operation_id=op_credit,
                    operation_type="buyout_sale",
                    source="economy.buyout",
                    item_meta={"resource_code": resource.code, "resource_id": str(resource.id), "amount": quantity},
                )
            except (httpx.HTTPStatusError, httpx.HTTPError) as exc:
                # Откатить последний debit (ресурс уже списан, деньги не пришли)
                try:
                    await self.sell_use_case.mining_client.credit(resource.code, character_id, quantity, op_refund)
                except Exception as re:
                    logger.error("Refund debit failed for %s: %s", resource.code, re)
                raise HTTPException(status_code=502, detail="External service error during bulk sell") from exc

            stock = await session.scalar(
                select(BuyoutStock).where(BuyoutStock.resource_id == resource.id).with_for_update()
            )
            if stock is None:
                stock = BuyoutStock(resource_id=resource.id, quantity=0)
                session.add(stock)
            stock.quantity += quantity

            transaction = EconomyTransaction(
                transaction_type=TransactionType.BUYOUT_SELL,
                resource_id=resource.id,
                quantity=quantity,
                price_per_unit=price.buy_price,
                total=item_total_price,
                buyer_id=None,
                seller_id=character_id,
                lot_id=None,
            )
            session.add(transaction)
            await session.flush()

            results.append({
                "transaction_id": transaction.id,
                "resource_id": resource.id,
                "quantity": quantity,
                "price_per_unit": price.buy_price,
                "total_price": item_total_price,
                "operation_id": op_credit,
            })
        
        # Сохраняем изменения стока и транзакций в БД
        await session.commit()

        # ОДНО агрегированное сообщение
        try:
            location_slug = await self.sell_use_case.characters_client.get_character_location(character_id)
        except Exception:
            location_slug = "unknown"
        
        try:
            items_list = ", ".join(resources_parts)
            message_text = self.sell_use_case.template_service.get_buyout_sell_message(
                items_list=items_list,
                price=str(total_price),
            )
            await self.sell_use_case.economy_events.publish_message(
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
            await self.sell_use_case.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "buyout_stock_updated",
                    "location_slug": location_slug,   
                    "initiator_character_id": str(character_id),
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish buyout_stock_updated: {e}")
        
        return results