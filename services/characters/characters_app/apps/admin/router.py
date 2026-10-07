import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status

from shared.schemas.auth import UserTokenDataReadSchema

from ...core.db import Session
from ..characters.routes.economy import _change_character_currency
from ..characters.schemas import (
    CharacterCurrencyOperationFilters, CharacterCurrencyOperationListSchema,
    CharacterCurrencyOperationRequest, CharacterCurrencyOperationResponse,
    CharacterTradePrivilegeReadSchema, CharacterTradePrivilegesInternalSchema,
    CharacterTradePrivilegeUpdateSchema,
)
from ..characters.deps import get_character_trade_privileges_use_case
from ..characters.use_cases.trade_privileges.get import GetCharacterTradePrivilegesUseCaseProtocol
from .depends import (
    get_admin_ban_all_by_user_use_case,
    get_admin_ban_character_use_case,
    get_admin_get_characters_by_user_use_case,
    get_admin_search_characters_use_case,
    get_admin_unban_all_by_user_use_case,
    get_admin_unban_character_use_case,
    get_character_currency_operations_use_case,
    get_reset_character_distributions_use_case,
    get_update_character_trade_privileges_use_case,
    require_admin,
)
from .use_cases.currency_operations import GetCharacterCurrencyOperationsUseCaseProtocol
from .use_cases.update_trade_privileges import UpdateCharacterTradePrivilegesUseCaseProtocol
from .schemas import (
    AdminBanCharacterRequest, AdminChangeDucatsRequest, AdminCharacterListSchema,
    AdminCharacterReadSchema, AdminCharacterSearchFilters,
)
from .use_cases.admin_ban_all_by_user import AdminBanAllByUserUseCaseProtocol
from .use_cases.admin_ban_character import AdminBanCharacterUseCaseProtocol
from .use_cases.admin_get_characters_by_user import AdminGetCharactersByUserUseCaseProtocol
from .use_cases.admin_search_characters import AdminSearchCharactersUseCaseProtocol
from .use_cases.admin_unban_all_by_user import AdminUnbanAllByUserUseCaseProtocol
from .use_cases.admin_unban_character import AdminUnbanCharacterUseCaseProtocol
from .use_cases.reset_character_distributions import ResetCharacterDistributionsUseCaseProtocol


router = APIRouter(
    prefix='/api/characters',
    tags=['Characters Admin'],
    dependencies=[Depends(require_admin)],
)


@router.get('/admin/characters/currency-operations', response_model=CharacterCurrencyOperationListSchema)
async def get_character_currency_operations(
    filters: CharacterCurrencyOperationFilters = Depends(),
    use_case: GetCharacterCurrencyOperationsUseCaseProtocol = Depends(get_character_currency_operations_use_case),
) -> CharacterCurrencyOperationListSchema:
    return await use_case(filters)

# ---- ADMIN: Поиск персонажей ----
@router.get('/admin/characters/search', response_model=AdminCharacterListSchema)
async def admin_search_characters(
    filters: AdminCharacterSearchFilters = Depends(),
    use_case: AdminSearchCharactersUseCaseProtocol = Depends(get_admin_search_characters_use_case),
) -> AdminCharacterListSchema:
    return await use_case(filters)


# ---- ADMIN: Детали персонажа ----
@router.get('/admin/characters/{character_id}', response_model=AdminCharacterReadSchema)
async def admin_get_character(
    character_id: uuid.UUID = Path(...),
    use_case: AdminSearchCharactersUseCaseProtocol = Depends(get_admin_search_characters_use_case),
) -> AdminCharacterReadSchema:
    filters = AdminCharacterSearchFilters(character_id=character_id, limit=1)
    result = await use_case(filters)
    if not result.objects:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found')
    return result.objects[0]


# ---- ADMIN: Изменение дукатов ----
@router.post('/admin/characters/{character_id}/ducats', response_model=CharacterCurrencyOperationResponse)
async def admin_change_ducats(
    data: AdminChangeDucatsRequest,
    session: Session,
    character_id: uuid.UUID = Path(...),
    admin: UserTokenDataReadSchema = Depends(require_admin),
) -> CharacterCurrencyOperationResponse:
    
    operation_id = uuid.uuid4()
    
    operation_type = 'admin_credit' if data.amount > 0 else 'admin_debit'
    
    request_data = CharacterCurrencyOperationRequest(
        operation_id=operation_id,
        amount=abs(data.amount),
        operation_type=operation_type,
        source='admin.panel',
        meta={'reason': data.reason, 'admin_user_id': str(admin.user_id)} if data.reason else {'admin_user_id': str(admin.user_id)},
    )
    
    return await _change_character_currency(
        session=session,
        character_id=character_id,
        currency='ducats',
        data=request_data,
        operation_type='credit' if data.amount > 0 else 'debit',
    )


# ---- ADMIN: Бан персонажа ----
@router.post('/admin/characters/{character_id}/ban', response_model=AdminCharacterReadSchema)
async def admin_ban_character(
    data: AdminBanCharacterRequest,
    character_id: uuid.UUID = Path(...),
    use_case: AdminBanCharacterUseCaseProtocol = Depends(get_admin_ban_character_use_case),
) -> AdminCharacterReadSchema:
    try:
        return await use_case(character_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found') from exc


# ---- ADMIN: Разбан персонажа ----
@router.post('/admin/characters/{character_id}/unban', response_model=AdminCharacterReadSchema)
async def admin_unban_character(
    character_id: uuid.UUID = Path(...),
    use_case: AdminUnbanCharacterUseCaseProtocol = Depends(get_admin_unban_character_use_case),
) -> AdminCharacterReadSchema:
    try:
        return await use_case(character_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found') from exc

# ---- ADMIN: Все персонажи аккаунта ----
@router.get('/admin/users/{user_id}/characters', response_model=list[AdminCharacterReadSchema])
async def admin_get_characters_by_user(
    user_id: uuid.UUID = Path(...),
    use_case: AdminGetCharactersByUserUseCaseProtocol = Depends(get_admin_get_characters_by_user_use_case),
) -> list[AdminCharacterReadSchema]:
    return await use_case(user_id)


# ---- ADMIN: Бан всех персонажей аккаунта ----
@router.post('/admin/users/{user_id}/ban-all', response_model=list[AdminCharacterReadSchema])
async def admin_ban_all_by_user(
    user_id: uuid.UUID = Path(...),
    use_case: AdminBanAllByUserUseCaseProtocol = Depends(get_admin_ban_all_by_user_use_case),
) -> list[AdminCharacterReadSchema]:
    try:
        return await use_case(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No characters found for user') from exc


# ---- ADMIN: Разбан всех персонажей аккаунта ----
@router.post('/admin/users/{user_id}/unban-all', response_model=list[AdminCharacterReadSchema])
async def admin_unban_all_by_user(
    user_id: uuid.UUID = Path(...),
    use_case: AdminUnbanAllByUserUseCaseProtocol = Depends(get_admin_unban_all_by_user_use_case),
) -> list[AdminCharacterReadSchema]:
    try:
        return await use_case(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No characters found for user') from exc


# ---- ADMIN: Trade privileges ----
@router.get(
    '/admin/characters/{character_id}/trade-privileges',
    response_model=CharacterTradePrivilegesInternalSchema,
)
async def get_character_trade_privileges_admin(
    character_id: uuid.UUID = Path(...),
    use_case: GetCharacterTradePrivilegesUseCaseProtocol = Depends(get_character_trade_privileges_use_case),
) -> CharacterTradePrivilegesInternalSchema:
    return await use_case(character_id)

@router.patch(
    '/admin/characters/{character_id}/trade-privileges',
    response_model=CharacterTradePrivilegeReadSchema,
)
async def update_character_trade_privileges(
    data: CharacterTradePrivilegeUpdateSchema,
    character_id: uuid.UUID = Path(...),
    admin: UserTokenDataReadSchema = Depends(require_admin),
    use_case: UpdateCharacterTradePrivilegesUseCaseProtocol = Depends(get_update_character_trade_privileges_use_case),
) -> CharacterTradePrivilegeReadSchema:
    try:
        return await use_case(character_id, data, admin.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found') from exc


# ---- ADMIN: Сброс распределений ----
@router.post('/{character_id}/reset-distributions', response_model=bool)
async def get_reset_character_distributions(
    character_id: uuid.UUID = Path(...),
    use_case: ResetCharacterDistributionsUseCaseProtocol = Depends(get_reset_character_distributions_use_case)
) -> bool:
    return await use_case(character_id)
