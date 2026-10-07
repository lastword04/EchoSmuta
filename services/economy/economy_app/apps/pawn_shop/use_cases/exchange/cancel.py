import uuid
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from ...models import ExchangeLot, LotStatus, LotType, Resource, EconomyTransaction, TransactionType
from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...events.economy import EconomyEventsProtocol
from .utils import raise_external_error
import logging

logger = logging.getLogger(__name__)


class CancelExchangeLotUseCase:
    def __init__(self, 
                 characters_client: CharactersClient, 
                 mining_client: MiningClient,
                 economy_events: EconomyEventsProtocol) -> None:  
        self.characters_client = characters_client
        self.mining_client = mining_client
        self.economy_events = economy_events

    async def __call__(self, lot_id: uuid.UUID, character_id: uuid.UUID, session: AsyncSession) -> dict[str, Any]:
        lot = await session.scalar(select(ExchangeLot).where(ExchangeLot.id == lot_id).with_for_update())
        if lot is None:
            raise HTTPException(status_code=404, detail="Lot not found")
        if lot.owner_character_id != character_id:
            raise HTTPException(status_code=403, detail="Only owner can cancel lot")
        if lot.status != LotStatus.ACTIVE:
            raise HTTPException(status_code=409, detail="Lot is already closed")

        items = list(lot.items)
        resources = (await session.scalars(
            select(Resource).where(Resource.id.in_([i.resource_id for i in items]))
        )).all()
        resource_map = {r.id: r for r in resources}

        operation_id = uuid.uuid4()
        try:
            if lot.lot_type == LotType.SELL:
                # Возвращаем владельцу ВСЕ ресурсы
                for item in items:
                    resource = resource_map[item.resource_id]
                    await self.mining_client.credit(
                        resource.code,
                        character_id,
                        item.quantity,
                        uuid.uuid5(operation_id, f"credit-{resource.code}"),
                    )
            else:
                # Возвращаем владельцу всю цену
                await self.characters_client.credit(
                    character_id,
                    lot.price,
                    operation_id=operation_id,
                    operation_type="exchange_cancel_refund",
                    source="economy.exchange",
                    item_meta={"lot_id": str(lot.id)},
                )
        except httpx.HTTPStatusError as exc:
            raise_external_error(exc, "External service rejected exchange lot cancellation")
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        lot.status = LotStatus.CANCELLED     
       
        for item in items:
            if lot.lot_type == LotType.SELL:
                # Игрок отменил продажу: ресурсы возвращаются ему, денег в сделке уже не было
                session.add(EconomyTransaction(
                    transaction_type=TransactionType.EXCHANGE_CANCEL,
                    resource_id=item.resource_id,
                    quantity=item.quantity,
                    price_per_unit=Decimal("0"),
                    total=Decimal("0"),
                    buyer_id=None,
                    seller_id=character_id,
                    lot_id=lot.id,
                ))
            else:  # LotType.BUY
                # Игрок отменил покупку: деньги возвращаются ему. 
                # Так как resource_id обязателен, используем ресурс из лота для записи
                price_per_item = lot.price / len(items) if items else Decimal("0")
                session.add(EconomyTransaction(
                    transaction_type=TransactionType.EXCHANGE_CANCEL,
                    resource_id=item.resource_id,
                    quantity=item.quantity,
                    price_per_unit=price_per_item,
                    total=price_per_item * item.quantity,
                    buyer_id=character_id,
                    seller_id=None,
                    lot_id=lot.id,
                ))     
        
        await session.commit()

        try:
            location_slug = await self.characters_client.get_character_location(character_id)
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "lot_cancelled",
                    "lot_id": str(lot.id),
                    "location_slug": location_slug,
                    "initiator_character_id": str(character_id),
                },
            )
        except Exception as e:
            logger.warning("Failed to publish lot_cancelled event: %s", e)

        return {"lot_id": lot.id, "status": lot.status, "operation_id": operation_id}