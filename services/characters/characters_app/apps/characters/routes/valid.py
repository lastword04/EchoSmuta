"""Валидация персонажа: проверка онлайн-статуса."""
import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.characters import CharacterOnlineStatus
from ....core.depends import get_service_token_payload
from ..use_cases.valid.get_is_online import GetIsOnlineCharacterUseCaseProtocol
from ..deps import get_get_online_status_use_case

router = APIRouter()


@router.get('/{character_id}/is-online', response_model=CharacterOnlineStatus)
async def get_my_online_status(
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: GetIsOnlineCharacterUseCaseProtocol = Depends(get_get_online_status_use_case)
) -> CharacterOnlineStatus:
    return await use_case(character_id)