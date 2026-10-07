import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from shared.schemas.auth import UserTokenDataReadSchema

from ...core.db import Session
from ...core.depends import get_user_token_payload
from ...core.clients.depends import get_mining_client
from ...core.clients.mining_client import MiningClient
from .models import BuyoutStock, CurrentPrice, ExchangeLot, Resource
from .schemas import LotCreateRequest, LotRead, ResourceRead, TradeRequest, BulkTradeRequest
from .service import get_price, list_lots
from .use_cases.buyout.buy import BuyResourceFromBuyoutUseCase
from .use_cases.buyout.sell import SellResourceToBuyoutUseCase
from .use_cases.buyout.buy_resources_bulk import BuyResourcesBulkUseCase
from .use_cases.buyout.sell_resources_bulk import SellResourcesBulkUseCase
from .use_cases.buyout.depends import get_buy_resource_from_buyout_use_case, get_sell_resource_to_buyout_use_case
from .use_cases.exchange.cancel import CancelExchangeLotUseCase
from .use_cases.exchange.create import CreateExchangeLotUseCase
from .use_cases.exchange.deal import DealExchangeLotUseCase
from .use_cases.exchange.depends import (
    get_cancel_exchange_lot_use_case,
    get_create_exchange_lot_use_case,
    get_deal_exchange_lot_use_case,
)

router = APIRouter(prefix="/api/economy", tags=["Economy"])


@router.get("/buyout/resources", response_model=list[ResourceRead])
async def buyout_resources(
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    mining_client: MiningClient = Depends(get_mining_client),
) -> list[ResourceRead]:
    # 1. Используем outerjoin для обеих таблиц
    query = (
        select(Resource, CurrentPrice, BuyoutStock)
        .outerjoin(CurrentPrice, CurrentPrice.resource_id == Resource.id)
        .outerjoin(BuyoutStock, BuyoutStock.resource_id == Resource.id)
        .where(Resource.is_tradeable.is_(True))
        .order_by(Resource.order)
    )
    rows = await session.execute(query)

    player_resources = {}
    if token.character_id:
        try:
            payload = await mining_client.get_player_resources(token.character_id)
            # Ожидаемый формат: {"resources": [{"resource_slug": "...", "amount": ...}]}
            for item in payload.get("resources", []):
                player_resources[item["resource_slug"]] = int(item.get("amount", 0))
        except Exception:
            # Если mining не отвечает, оставляем пустой словарь (будет 0)
            pass
    
    result = []
    for r, p, s in rows:
        player_qty = player_resources.get(r.code, 0)
        result.append(ResourceRead(
            id=r.id,
            code=r.code,
            name=r.name,
            icon_url=r.icon_url,
            player_quantity=Decimal(str(player_qty)),
            sell_price=p.sell_price if p else r.base_sell_price,
            buy_price=p.buy_price if p else r.base_buy_price,
            buyout_stock_quantity=s.quantity if s else Decimal("0"),
            next_recalculation_at=p.next_recalculation_at if p else None,
            category=r.category,
        ))
    return result

@router.post("/buyout/buy")
async def buyout_buy(
    data: TradeRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuyResourceFromBuyoutUseCase = Depends(get_buy_resource_from_buyout_use_case),
) -> dict:
    if token.character_id is None:
        raise ValueError("Character is required")
    return await use_case(data, token.character_id, session)


@router.post("/buyout/buy-bulk")
async def buyout_buy_bulk(
    data: BulkTradeRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    buy_use_case: BuyResourceFromBuyoutUseCase = Depends(get_buy_resource_from_buyout_use_case),
) -> list[dict]:
    """Покупает несколько ресурсов одним запросом."""
    if token.character_id is None:
        raise HTTPException(status_code=401, detail="Character is required")
    
    bulk_use_case = BuyResourcesBulkUseCase(buy_use_case)
    return await bulk_use_case(data, token.character_id, session)


@router.post("/buyout/sell")
async def buyout_sell(
    data: TradeRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: SellResourceToBuyoutUseCase = Depends(get_sell_resource_to_buyout_use_case),
) -> dict:
    if token.character_id is None:
        raise ValueError("Character is required")
    return await use_case(data, token.character_id, session)


@router.post("/buyout/sell-bulk")
async def buyout_sell_bulk(
    data: BulkTradeRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    sell_use_case: SellResourceToBuyoutUseCase = Depends(get_sell_resource_to_buyout_use_case),
) -> list[dict]:
    """Продаёт несколько ресурсов одним запросом."""
    if token.character_id is None:
        raise HTTPException(status_code=401, detail="Character is required")
    
    bulk_use_case = SellResourcesBulkUseCase(sell_use_case)
    return await bulk_use_case(data, token.character_id, session)


@router.get("/exchange/lots", response_model=list[LotRead])
async def exchange_lots(session: Session, resource_id: uuid.UUID | None = Query(None)) -> list[ExchangeLot]:
    return await list_lots(session, resource_id)


@router.post("/exchange/lots", response_model=LotRead)
async def exchange_create(
    data: LotCreateRequest,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateExchangeLotUseCase = Depends(get_create_exchange_lot_use_case),
) -> ExchangeLot:
    if token.character_id is None:
        raise ValueError("Character is required")
    return await use_case(data, token.character_id, session)


@router.post("/exchange/lots/{lot_id}/deal")
async def exchange_deal(
    lot_id: uuid.UUID,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DealExchangeLotUseCase = Depends(get_deal_exchange_lot_use_case),
) -> dict:
    if token.character_id is None:
        raise ValueError("Character is required")
    return await use_case(lot_id, token.character_id, session)


@router.delete("/exchange/lots/{lot_id}", status_code=204)
async def exchange_cancel_delete(
    lot_id: uuid.UUID,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CancelExchangeLotUseCase = Depends(get_cancel_exchange_lot_use_case),
) -> None:
    if token.character_id is None:
        raise ValueError("Character is required")
    await use_case(lot_id, token.character_id, session)


@router.post("/exchange/lots/{lot_id}/cancel")
async def exchange_cancel(
    lot_id: uuid.UUID,
    session: Session,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CancelExchangeLotUseCase = Depends(get_cancel_exchange_lot_use_case),
) -> dict:
    if token.character_id is None:
        raise ValueError("Character is required")
    return await use_case(lot_id, token.character_id, session)
