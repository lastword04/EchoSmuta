import uuid
from fastapi import APIRouter, Depends, Path
from shared.schemas.base import StatusOkSchema
from .schemas import ApplyBuffSchema, RemoveBuffSchema, CharacterBuffsResponseSchema, ConsumeFoodSchema
from .depends import (
    get_apply_buff_use_case,
    get_remove_buff_use_case,
    get_character_buffs_use_case,
    get_consume_food_use_case
)
from .use_cases.apply_buff import ApplyBuffUseCaseProtocol
from .use_cases.remove_buff import RemoveBuffUseCaseProtocol
from .use_cases.get_buffs import GetCharacterBuffsUseCaseProtocol
from .use_cases.consume_food import ConsumeFoodUseCaseProtocol


router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.post("/buffs/apply", response_model=StatusOkSchema)
async def apply_buff(
    data: ApplyBuffSchema,
    use_case: ApplyBuffUseCaseProtocol = Depends(get_apply_buff_use_case)
) -> StatusOkSchema:
    """Применить бафф к персонажу (вызывается из mining)"""
    await use_case(data)
    return StatusOkSchema()


@router.post("/buffs/remove", response_model=StatusOkSchema)
async def remove_buff(
    data: RemoveBuffSchema,
    use_case: RemoveBuffUseCaseProtocol = Depends(get_remove_buff_use_case)
) -> StatusOkSchema:
    """Удалить бафф"""
    await use_case(data.character_id, data.buff_type)
    return StatusOkSchema()


@router.get("/{character_id}/buffs", response_model=CharacterBuffsResponseSchema)
async def get_character_buffs(
    character_id: uuid.UUID = Path(...),
    use_case: GetCharacterBuffsUseCaseProtocol = Depends(get_character_buffs_use_case)
) -> CharacterBuffsResponseSchema:
    """Получить активные баффы персонажа"""
    return await use_case(character_id)


@router.post("/food/consume", response_model=StatusOkSchema)
async def consume_food(
    data: ConsumeFoodSchema,
    use_case: ConsumeFoodUseCaseProtocol = Depends(get_consume_food_use_case)
) -> StatusOkSchema:
    """Применить еду (рыба, блюда Харчевни)"""
    await use_case(data)
    return StatusOkSchema()