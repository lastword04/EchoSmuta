"""Внутренние (межсервисные) endpoint'ы characters-сервиса."""
import uuid

from fastapi import APIRouter, Depends, Path, Query
import sqlalchemy as sa
from sqlalchemy import select

from shared.schemas.base import StatusOkSchema

from ....core.db import Session
from ....core.depends import get_service_token_payload
from ..models import Character
from ..schemas import (
    CharacterTradePrivilegesInternalSchema,
    InternalCharacterSearchItemSchema, InternalCharacterSearchResponseSchema,
    EquipmentBonusesRequestSchema,
)
from ..use_cases.trade_privileges.get import GetCharacterTradePrivilegesUseCaseProtocol
from ..use_cases.skills.recalculate_equipment_bonuses import RecalculateEquipmentBonusesUseCaseProtocol
from ...rest.repositories.house_furniture_repository import HouseFurnitureRepository
from ..deps import (
    get_character_trade_privileges_use_case,
    get_recalculate_equipment_bonuses_use_case,
)

router = APIRouter()


@router.get('/internal/characters/search', response_model=InternalCharacterSearchResponseSchema)
async def search_characters_internal(
    session: Session,
    token: dict = Depends(get_service_token_payload),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(50, gt=0, le=50),
    offset: int = Query(0, ge=0),
) -> InternalCharacterSearchResponseSchema:
    filters = []
    if search:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        filters.append(Character.name.ilike(f"%{escaped_search}%", escape="\\"))

    characters_statement = (
        select(Character)
        .where(*filters)
        .order_by(Character.name.asc())
        .offset(offset)
        .limit(limit)
    )
    count_statement = select(sa.func.count()).select_from(Character).where(*filters)
    characters = (await session.scalars(characters_statement)).all()
    count = await session.scalar(count_statement)
    return InternalCharacterSearchResponseSchema(
        objects=[InternalCharacterSearchItemSchema.model_validate(character) for character in characters],
        count=count or 0,
    )


@router.get(
    '/internal/characters/{character_id}/trade-privileges',
    response_model=CharacterTradePrivilegesInternalSchema,
)
async def get_character_trade_privileges(
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: GetCharacterTradePrivilegesUseCaseProtocol = Depends(get_character_trade_privileges_use_case),
) -> CharacterTradePrivilegesInternalSchema:
    return await use_case(character_id)


# Equipment Bonuses Endpoints

@router.post(
    "/internal/characters/{character_id}/equipment/recalculate",
    response_model=StatusOkSchema,
    summary="Пересчитать бонусы экипировки (internal)",
    description="Внутренний endpoint для пересчёта бонусов экипировки. Требует service token."
)
async def recalculate_equipment_bonuses(
    character_id: uuid.UUID,
    request: EquipmentBonusesRequestSchema,
    token: dict = Depends(get_service_token_payload),
    use_case: RecalculateEquipmentBonusesUseCaseProtocol = Depends(get_recalculate_equipment_bonuses_use_case)
) -> StatusOkSchema:
    """
    Пересчитывает бонусы экипировки персонажа (только для межсервисных вызовов).

    Требует service token.
    """
    return await use_case(character_id, request.bonuses)


@router.get(
    '/internal/houses/furniture/inventory-item-ids',
    summary="Список inventory_item_id, установленных в домах (internal)",
    description="Внутренний endpoint для mining: какие предметы сейчас стоят в домах. Требует service token.",
)
async def get_installed_furniture_item_ids(
    session: Session,
    token: dict = Depends(get_service_token_payload),
) -> dict:
    repo = HouseFurnitureRepository(session=session)
    ids = await repo.get_all_inventory_item_ids()
    return {"inventory_item_ids": [str(i) for i in ids]}
