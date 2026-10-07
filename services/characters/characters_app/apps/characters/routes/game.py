"""Игровые сессии: вход/выход персонажа в игру."""
import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import CharacterReadSchema, CharacterListIds

from ....core.depends import get_service_token_payload
from ..adapters.mining import MiningServiceClientProtocol
from ..use_cases.game.play import CharacterJoinToGameUseCaseProtocol
from ..use_cases.game.play_main import CharacterJoinMainToGameUseCaseProtocol
from ..use_cases.game.quit import CharacterQuitFromGameUseCaseProtocol
from ..use_cases.game.quit_all import CharacterQuitAllFromGameUseCaseProtocol
from ..use_cases.skills.recalculate_equipment_bonuses import RecalculateEquipmentBonusesUseCaseProtocol
from ..deps import (
    get_character_join_to_game_use_case,
    get_character_join_main_to_game_use_case,
    get_character_quit_from_game_use_case,
    get_character_quit_all_from_game_use_case,
    get_recalculate_equipment_bonuses_use_case,
    get_mining_adapter,
)

router = APIRouter()


@router.post('/main/user/{user_id}/play', response_model=CharacterReadSchema)
async def play_main(
    user_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: CharacterJoinMainToGameUseCaseProtocol = Depends(get_character_join_main_to_game_use_case)
) -> CharacterReadSchema:
    return await use_case(user_id)

@router.post('/all/user/{user_id}/quit', response_model=CharacterListIds)
async def quit_all(
    user_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: CharacterQuitAllFromGameUseCaseProtocol = Depends(get_character_quit_all_from_game_use_case)
) -> StatusOkSchema:
    return await use_case(user_id)

@router.post('/{character_id}/user/{user_id}/play', response_model=CharacterReadSchema)
async def play(
    character_id: uuid.UUID = Path(...),
    user_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: CharacterJoinToGameUseCaseProtocol = Depends(get_character_join_to_game_use_case),
    mining_adapter: MiningServiceClientProtocol = Depends(get_mining_adapter),
    recalc_use_case: RecalculateEquipmentBonusesUseCaseProtocol = Depends(get_recalculate_equipment_bonuses_use_case)
) -> CharacterReadSchema:
    # Основная логика входа в игру
    result = await use_case(character_id, user_id)

    # НОВОЕ: Recovery механизм (страховка) - пересчёт бонусов экипировки при входе
    try:
        bonuses = await mining_adapter.get_equipment_bonuses(character_id)
        await recalc_use_case(character_id, bonuses)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to fetch equipment bonuses for character {character_id} on login: {e}")
        # НЕ блокируем вход, продолжаем

    return result

@router.post('/{character_id}/user/{user_id}/quit', response_model=CharacterReadSchema)
async def quit(
    character_id: uuid.UUID = Path(...),
    user_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: CharacterQuitFromGameUseCaseProtocol = Depends(get_character_quit_from_game_use_case)
) -> StatusOkSchema:
    return await use_case(character_id, user_id)
