from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.info.characters_info import (
    CharacterInfoRepositoryProtocol,
    CharacterInfoRepository,
)
from ..services.info.characters_info import (
    CharacterInfoServiceProtocol,
    CharacterInfoService,
)
from ..use_cases.characters_info.get_my_info import (
    GetMyCharactersInfoUseCaseProtocol,
    GetMyCharacterInfoUseCase,
)
from ..use_cases.characters_info.update_my_info import (
    UpdateMyCharactersInfoUseCaseProtocol,
    UpdateMyCharacterInfoUseCase,
)


def __get_character_info_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterInfoRepositoryProtocol:
    return CharacterInfoRepository(session)


def get_character_info_service(repository: CharacterInfoRepositoryProtocol = Depends(__get_character_info_repository)) -> CharacterInfoServiceProtocol:
    return CharacterInfoService(repository)


def get_get_my_characters_info_use_case(service: CharacterInfoServiceProtocol = Depends(get_character_info_service)) -> GetMyCharactersInfoUseCaseProtocol:
    return GetMyCharacterInfoUseCase(service)


def get_update_my_characters_info_use_case(service: CharacterInfoServiceProtocol = Depends(get_character_info_service)) -> UpdateMyCharactersInfoUseCaseProtocol:
    return UpdateMyCharacterInfoUseCase(service)
