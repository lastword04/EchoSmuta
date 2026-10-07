"""Навыки и распределение очков персонажа."""
from fastapi import APIRouter, Depends

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema

from ..schemas import (
    AppliedCharacterHistoryCreateSchema, ChangeSkillsRequest, ChangeSkillsResponse,
    AllCharacterDistributionInfo, CharacterAbilitySkillsReadSchema,
)
from ..use_cases.skills.calculate_stats_for_ability_skills import CalculateStatsForChangeUseCaseProtocol
from ..use_cases.skills.add_stats_by_ability_skills import AddStatsToCharacterUseCaseProtocol
from ..use_cases.skills.update_stats_by_ability_skills import UpdateStatsToCharacterUseCaseProtocol
from ..use_cases.skills.get_applied_skills_by_character import AppliedCharacterHistoryUseCaseProtocol
from ..use_cases.skills.get_ability_by_character import GetMyCharacterAbilitySkillsUseCaseProtocol
from ....core.depends import get_user_token_payload
from ..deps import (
    get_calculate_character_stats_use_case,
    get_add_stats_by_ability_skills_use_case,
    get_update_stats_by_ability_skills_use_case,
    get_get_applied_skills_by_character,
    get_get_ability_by_character,
)

router = APIRouter()


@router.post('/skills-calculate/', response_model=ChangeSkillsResponse)
async def calculate_stats_for_change(
    data: ChangeSkillsRequest,
    token: dict = Depends(get_user_token_payload),
    use_case: CalculateStatsForChangeUseCaseProtocol = Depends(get_calculate_character_stats_use_case)
) -> ChangeSkillsResponse:
    return await use_case(token, data)

@router.post('/skills-add/', response_model=CharacterReadSchema)
async def add_stats_by_ability_skills(
    history: AppliedCharacterHistoryCreateSchema,
    token: dict = Depends(get_user_token_payload),
    use_case: AddStatsToCharacterUseCaseProtocol = Depends(get_add_stats_by_ability_skills_use_case)
) -> CharacterReadSchema:
    return await use_case(token, history)

@router.post('/skills-update/', response_model=CharacterReadSchema)
async def update_stats_by_ability_skills(
    history: AppliedCharacterHistoryCreateSchema,
    token: dict = Depends(get_user_token_payload),
    use_case: UpdateStatsToCharacterUseCaseProtocol = Depends(get_update_stats_by_ability_skills_use_case)
) -> CharacterReadSchema:
    return await use_case(token, history)

@router.get('/applied-skills/', response_model=AllCharacterDistributionInfo)
async def get_applied_character_history(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AppliedCharacterHistoryUseCaseProtocol = Depends(get_get_applied_skills_by_character)
) -> AllCharacterDistributionInfo:
    return await use_case(token)

@router.get('/skills/', response_model=CharacterAbilitySkillsReadSchema)
async def get_character_ability_skills(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyCharacterAbilitySkillsUseCaseProtocol = Depends(get_get_ability_by_character)
) -> CharacterAbilitySkillsReadSchema:
    return await use_case(token)
