"""Привязка / отвязка персонажей."""
import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema

from ..schemas import CharacterAttachmentSettingsReadSchema
from ..use_cases.attachment.get_character_attachment_settings import GetCharacterAttachmentSettingsUseCaseProtocol
from ..use_cases.attachment.detach_character import DetachCharacterUseCaseProtocol
from ..use_cases.attachment.attach_character import AttachCharacterUseCaseProtocol
from ..use_cases.attachment.has_detach_characters import HasDetachCharacterStatusUseCaseProtocol
from ..use_cases.attachment.get_detached_characters import GetDetachCharacterStatusUseCaseProtocol
from ....core.depends import get_user_token_payload
from ..deps import (
    get_character_attachment_settings_use_case_dep,
    get_detach_character_use_case,
    get_attach_character_use_case,
    get_has_detach_character_status_use_case,
    get_get_detached_characters_use_case,
)

router = APIRouter()


@router.get('/attachment-settings', response_model=CharacterAttachmentSettingsReadSchema)
async def get_character_attachment_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharacterAttachmentSettingsUseCaseProtocol = Depends(get_character_attachment_settings_use_case_dep)
) -> CharacterAttachmentSettingsReadSchema:
    return await use_case()

@router.get('/detach', response_model=bool)
async def has_detached_characters(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: HasDetachCharacterStatusUseCaseProtocol = Depends(get_has_detach_character_status_use_case)
) -> bool:
    return await use_case(token)

@router.get('/detach/all', response_model=list[CharacterReadSchema])
async def get_detached_characters(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetDetachCharacterStatusUseCaseProtocol = Depends(get_get_detached_characters_use_case)
) -> list[CharacterReadSchema]:
    return await use_case(token)

@router.delete('/detach/{character_id}', response_model=None, status_code=204)
async def detach_character(character_id: uuid.UUID = Path(...),
                            token: UserTokenDataReadSchema = Depends(get_user_token_payload),
                            use_case: DetachCharacterUseCaseProtocol = Depends(get_detach_character_use_case)
                            ) -> None:
     await use_case(token, character_id)
     return None

@router.post('/attach/{character_id}', response_model=bool, status_code=200)
async def attach_character(character_id: uuid.UUID = Path(...),
                           token: UserTokenDataReadSchema = Depends(get_user_token_payload),
                           use_case: AttachCharacterUseCaseProtocol = Depends(get_attach_character_use_case)
                           ) -> bool:
    return await use_case(token, character_id)
