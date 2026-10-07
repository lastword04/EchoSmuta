from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..repositories.mining.items import (
    CharacterItemsBalanceRepositoryProtocol,
    CharacterItemsBalanceRepository,
)
from ..services.character.characters import (
    CharacterWeightBalanceServiceProtocol,
    CharacterWeightBalanceService,
    UpdateCharacterWeightServiceProtocol,
    UpdateCharacterWeightService,
)
from ..services.mining.items import (
    CharacterItemsBalanceServiceProtocol,
    CharacterItemsBalanceService,
)
from ..use_cases.characters.mining.items.get_character_item_balance import (
    GetCharacterItemBalanceUseCaseProtocol,
    GetCharacterItemBalanceUseCase,
)
from ..use_cases.characters.mining.weight.get_character_weight_balance import (
    GetCharacterWeightBalanceUseCaseProtocol,
    GetCharacterWeightBalanceUseCase,
)
from ..use_cases.characters.update_weight import (
    UpdateCharacterWeightUseCaseProtocol,
    UpdateCharacterWeightUseCase,
)
from .valid import __get_character_repository


def __get_character_item_balance_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterItemsBalanceRepositoryProtocol:
    return CharacterItemsBalanceRepository(session=session)


def get_character_item_balance_service(repository: CharacterItemsBalanceRepositoryProtocol = Depends(__get_character_item_balance_repository)) -> CharacterItemsBalanceServiceProtocol:
    return CharacterItemsBalanceService(repository=repository)


def get_character_item_balance_use_case(service: CharacterItemsBalanceServiceProtocol = Depends(get_character_item_balance_service)) -> GetCharacterItemBalanceUseCaseProtocol:
    return GetCharacterItemBalanceUseCase(service=service)


# get character weight balance

def get_character_weight_balance_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository)) -> CharacterWeightBalanceServiceProtocol:
    return CharacterWeightBalanceService(repository=repository)


def get_character_weight_balance_use_case(service: CharacterWeightBalanceServiceProtocol = Depends(get_character_weight_balance_service)) -> GetCharacterWeightBalanceUseCaseProtocol:
    return GetCharacterWeightBalanceUseCase(service=service)


# update character weight

def get_character_update_weight_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository)) -> UpdateCharacterWeightServiceProtocol:
    return UpdateCharacterWeightService(repository=repository)


def get_character_update_weight_use_case(service: UpdateCharacterWeightServiceProtocol = Depends(get_character_update_weight_service)) -> UpdateCharacterWeightUseCaseProtocol:
    return UpdateCharacterWeightUseCase(service=service)
