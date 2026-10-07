from fastapi import Depends

from shared.permissions import ensure_admin
from shared.schemas.auth import UserTokenDataReadSchema

from ...core.db import AsyncSession, get_async_session
from ...core.depends import get_user_token_payload
from ..characters.deps import (
    get_character_currency_operation_service,
    get_character_events,
    get_character_trade_privilege_service,
    get_reset_character_distributions_service,
)
from ..characters.events.characters import CharacterEventsProtocol
from ..characters.services.economy.currency_operations import CharacterCurrencyOperationServiceProtocol
from ..characters.services.skills.reset_character_distributions import ResetCharacterDistributionsServiceProtocol
from ..characters.services.trade_privileges.trade_privileges import CharacterTradePrivilegeServiceProtocol
from .repositories.admin_characters import AdminCharacterRepository, AdminCharacterRepositoryProtocol
from .use_cases.admin_search_characters import AdminSearchCharactersUseCase, AdminSearchCharactersUseCaseProtocol
from .use_cases.admin_ban_character import AdminBanCharacterUseCase, AdminBanCharacterUseCaseProtocol
from .use_cases.admin_unban_character import AdminUnbanCharacterUseCase, AdminUnbanCharacterUseCaseProtocol
from .use_cases.admin_get_characters_by_user import AdminGetCharactersByUserUseCase, AdminGetCharactersByUserUseCaseProtocol
from .use_cases.admin_ban_all_by_user import AdminBanAllByUserUseCase, AdminBanAllByUserUseCaseProtocol
from .use_cases.admin_unban_all_by_user import AdminUnbanAllByUserUseCase, AdminUnbanAllByUserUseCaseProtocol
from .use_cases.currency_operations import GetCharacterCurrencyOperationsUseCase, GetCharacterCurrencyOperationsUseCaseProtocol
from .use_cases.reset_character_distributions import ResetCharacterDistributionsUseCase, ResetCharacterDistributionsUseCaseProtocol
from .use_cases.update_trade_privileges import UpdateCharacterTradePrivilegesUseCase, UpdateCharacterTradePrivilegesUseCaseProtocol


def __get_admin_character_repository(session: AsyncSession = Depends(get_async_session)) -> AdminCharacterRepositoryProtocol:
    return AdminCharacterRepository(session=session)


def get_admin_search_characters_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
) -> AdminSearchCharactersUseCaseProtocol:
    return AdminSearchCharactersUseCase(repository=repository)


def get_admin_ban_character_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
    character_events: CharacterEventsProtocol = Depends(get_character_events),
) -> AdminBanCharacterUseCaseProtocol:
    return AdminBanCharacterUseCase(repository=repository, character_events=character_events)


def get_admin_unban_character_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
    character_events: CharacterEventsProtocol = Depends(get_character_events),
) -> AdminUnbanCharacterUseCaseProtocol:
    return AdminUnbanCharacterUseCase(repository=repository, character_events=character_events)


def get_admin_get_characters_by_user_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
) -> AdminGetCharactersByUserUseCaseProtocol:
    return AdminGetCharactersByUserUseCase(repository=repository)


def get_admin_ban_all_by_user_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
    character_events: CharacterEventsProtocol = Depends(get_character_events),
) -> AdminBanAllByUserUseCaseProtocol:
    return AdminBanAllByUserUseCase(repository=repository, character_events=character_events)


def get_admin_unban_all_by_user_use_case(
    repository: AdminCharacterRepositoryProtocol = Depends(__get_admin_character_repository),
    character_events: CharacterEventsProtocol = Depends(get_character_events),
) -> AdminUnbanAllByUserUseCaseProtocol:
    return AdminUnbanAllByUserUseCase(repository=repository, character_events=character_events)


def require_admin(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
) -> UserTokenDataReadSchema:
    ensure_admin(token)
    return token


def get_reset_character_distributions_use_case(
    service: ResetCharacterDistributionsServiceProtocol = Depends(get_reset_character_distributions_service),
) -> ResetCharacterDistributionsUseCaseProtocol:
    return ResetCharacterDistributionsUseCase(service)


def get_update_character_trade_privileges_use_case(
    service: CharacterTradePrivilegeServiceProtocol = Depends(get_character_trade_privilege_service),
) -> UpdateCharacterTradePrivilegesUseCaseProtocol:
    return UpdateCharacterTradePrivilegesUseCase(service=service)


def get_character_currency_operations_use_case(
    service: CharacterCurrencyOperationServiceProtocol = Depends(get_character_currency_operation_service),
) -> GetCharacterCurrencyOperationsUseCaseProtocol:
    return GetCharacterCurrencyOperationsUseCase(service=service)
