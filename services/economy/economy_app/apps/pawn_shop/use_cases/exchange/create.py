import uuid
from typing import Any
from decimal import Decimal

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.clients.characters_client import CharactersClient
from .....core.clients.mining_client import MiningClient
from ...models import ExchangeLot, ExchangeLotItem, LotStatus, LotType, Resource
from ...schemas import LotCreateRequest
from ...events.economy import EconomyEventsProtocol
from .utils import raise_external_error
import logging

logger = logging.getLogger(__name__)


class CreateExchangeLotUseCase:
    def __init__(self, 
                 characters_client: CharactersClient, 
                 mining_client: MiningClient,
                 economy_events: EconomyEventsProtocol) -> None:  
        self.characters_client = characters_client
        self.mining_client = mining_client
        self.economy_events = economy_events

    async def __call__(self, data: LotCreateRequest, character_id: uuid.UUID, session: AsyncSession) -> ExchangeLot:
        # Загружаем все ресурсы бандла
        resource_ids = [item.resource_id for item in data.items]
        resources = (await session.scalars(
            select(Resource).where(Resource.id.in_(resource_ids))
        )).all()
        resource_map = {r.id: r for r in resources}
        for rid in resource_ids:
            if rid not in resource_map:
                raise HTTPException(status_code=404, detail="Resource not found")

        operation_id = uuid.uuid4()
        total = data.price

        lot = ExchangeLot(
            id=uuid.uuid4(),
            owner_character_id=character_id,
            lot_type=data.lot_type,
            status=LotStatus.ACTIVE,
            price=total,
        )

        # === БЛОК ВАЛИДАЦИИ ДО ТРАНЗАКЦИЙ ===
        if data.lot_type == LotType.SELL:
            # Продавец выставляет ресурсы — проверяем наличие КАЖДОГО
            try:
                payload = await self.mining_client.get_player_resources(character_id)
                resources_payload = payload.get("resources", payload if isinstance(payload, list) else [])
                amounts = {r.get("resource_slug"): int(r.get("amount", 0)) for r in resources_payload}
                for item in data.items:
                    resource = resource_map[item.resource_id]
                    current_amount = amounts.get(resource.code, 0)
                    if current_amount < item.quantity:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Недостаточно ресурса {resource.name}. Требуется: {item.quantity}, доступно: {current_amount}"
                        )
            except httpx.HTTPError:
                raise HTTPException(status_code=502, detail="Mining service is unavailable")
        else:
            # Покупатель размещает заявку — нужны дукаты на всю цену
            balance = await self.characters_client.get_balance(character_id)
            if balance < total:
                raise HTTPException(
                    status_code=409,
                    detail=f"Недостаточно дукатов для создания лота. Требуется: {total}, доступно: {balance}"
                )
        # === КОНЕЦ БЛОКА ВАЛИДАЦИИ ===

        # === ПРОВЕРКА МИНИМАЛЬНОЙ ЦЕНЫ ЛОТА ===
        MIN_LOT_VALUE_RATIO = Decimal("0.5")
        bundle_value = sum(
            Decimal(str(item.quantity)) * Decimal(str(resource_map[item.resource_id].base_sell_price))
            for item in data.items
        )
        min_price = (bundle_value * MIN_LOT_VALUE_RATIO).quantize(Decimal("0.01"))
        if Decimal(str(data.price)) < min_price:
            raise HTTPException(
                status_code=409,
                detail=f"Цена лота слишком низкая. Минимум: {min_price} дт."
            )
        # === КОНЕЦ ПРОВЕРКИ ===

        try:
            if data.lot_type == LotType.SELL:
                # Списываем каждый ресурс
                for item in data.items:
                    resource = resource_map[item.resource_id]
                    await self.mining_client.debit(
                        resource.code,
                        character_id,
                        item.quantity,
                        uuid.uuid5(operation_id, f"debit-{resource.code}"),
                    )
            elif data.lot_type == LotType.BUY:
                await self.characters_client.debit(
                    character_id,
                    total,
                    operation_id=operation_id,
                    operation_type="exchange_lot_create",
                    source="economy.exchange",
                    item_meta={"lot_id": str(lot.id)},
                )
            else:
                raise HTTPException(status_code=400, detail="Unsupported lot type")
        except httpx.HTTPStatusError as exc:
            raise_external_error(exc, "External service rejected exchange lot creation")
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="External service is unavailable") from exc

        session.add(lot)
        await session.flush()

        for item in data.items:
            session.add(ExchangeLotItem(
                lot_id=lot.id,
                resource_id=item.resource_id,
                quantity=item.quantity,
            ))

        await session.commit()
        await session.refresh(lot)

        try:
            location_slug = await self.characters_client.get_character_location(character_id)
            await self.economy_events.publish_state_update(
                event_type="economy_state_updated",
                payload={
                    "action": "lot_created",
                    "lot_id": str(lot.id),
                    "location_slug": location_slug,
                    "initiator_character_id": str(character_id),
                },
            )
        except Exception as e:
            logger.warning("Failed to publish lot_created event: %s", e)

        return lot