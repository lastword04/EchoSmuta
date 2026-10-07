"""Личная информация персонажа (my-info)."""
import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema

from ..schemas import CharacterInfoReadSchema, CharacterInfoRequestSchema
from ..use_cases.characters_info.get_my_info import GetMyCharactersInfoUseCaseProtocol
from ..use_cases.characters_info.update_my_info import UpdateMyCharactersInfoUseCaseProtocol
from ....core.depends import get_user_token_payload
from ..deps import (
    get_get_my_characters_info_use_case,
    get_update_my_characters_info_use_case,
)

router = APIRouter()


@router.get('/my-info', response_model=CharacterInfoReadSchema)
async def get_info(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyCharactersInfoUseCaseProtocol = Depends(get_get_my_characters_info_use_case)
) -> CharacterInfoReadSchema:
    return await use_case(token)

@router.put('/my-info/{info_id}', response_model=CharacterInfoReadSchema)
async def update_info(
    info_data: CharacterInfoRequestSchema,
    info_id: uuid.UUID = Path(...),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateMyCharactersInfoUseCaseProtocol = Depends(get_update_my_characters_info_use_case)
) -> CharacterInfoReadSchema:
    return await use_case(info_id, info_data, token)
