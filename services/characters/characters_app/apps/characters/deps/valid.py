from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.character.characters import CharacterRepositoryProtocol, CharacterRepository
from ..services.character.characters import GetIsOnlineCharacterServiceProtocol, GetIsOnlineCharacterService
from ..use_cases.valid.get_is_online import GetIsOnlineCharacterUseCaseProtocol, GetIsOnlineCharacterUseCase
from ..use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol, GetIsOnlineCharacterOrRaiseUseCase


def __get_character_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterRepositoryProtocol:
    """
    Функция для получения репозитория персонажей.
    """
    return CharacterRepository(session=session)


def get_character_is_online_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository)) -> GetIsOnlineCharacterServiceProtocol:
    return GetIsOnlineCharacterService(repository)


def get_get_online_status_use_case(service: GetIsOnlineCharacterServiceProtocol = Depends(get_character_is_online_service)) -> GetIsOnlineCharacterUseCaseProtocol:
    return GetIsOnlineCharacterUseCase(service)


def get_get_online_status_or_raise_use_case(service: GetIsOnlineCharacterServiceProtocol = Depends(get_character_is_online_service)) -> GetIsOnlineCharacterOrRaiseUseCaseProtocol:
    return GetIsOnlineCharacterOrRaiseUseCase(service)
