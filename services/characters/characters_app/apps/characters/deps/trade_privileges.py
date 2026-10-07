from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..adapters.mining import MiningServiceClientProtocol
from ..repositories.trade_privileges.trade_privileges import (
    CharacterTradePrivilegeRepositoryProtocol,
    CharacterTradePrivilegeRepository,
)
from ..services.trade_privileges.trade_privileges import (
    CharacterTradePrivilegeServiceProtocol,
    CharacterTradePrivilegeService,
)
from ..use_cases.trade_privileges.get import (
    GetCharacterTradePrivilegesUseCaseProtocol,
    GetCharacterTradePrivilegesUseCase,
)
from .adapters import get_mining_adapter


def get_character_trade_privilege_repository(
    session: AsyncSession = Depends(get_async_session),
) -> CharacterTradePrivilegeRepositoryProtocol:
    return CharacterTradePrivilegeRepository(session=session)


def get_character_trade_privilege_service(
    repository: CharacterTradePrivilegeRepositoryProtocol = Depends(get_character_trade_privilege_repository),
) -> CharacterTradePrivilegeServiceProtocol:
    return CharacterTradePrivilegeService(repository=repository)


def get_character_trade_privileges_use_case(
    service: CharacterTradePrivilegeServiceProtocol = Depends(get_character_trade_privilege_service),
    mining_client: MiningServiceClientProtocol = Depends(get_mining_adapter),
) -> GetCharacterTradePrivilegesUseCaseProtocol:
    return GetCharacterTradePrivilegesUseCase(service=service, mining_client=mining_client)
