from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.characters_chat.characters_chat import (
    CharacterChatRepositoryProtocol,
    CharacterChatRepository,
)
from ..services.characters_chat.characters_chat import (
    CharacterChatServiceProtocol,
    CharacterChatService,
)
from ..use_cases.characters_chat.get_online_characters import (
    GetOnlineCharactersUseCaseProtocol,
    GetOnlineCharactersUseCase,
)
from ..use_cases.characters_chat.get_by_ids import (
    GetCharactersByIdsUseCaseProtocol,
    GetCharactersByIdsUseCase,
)
from ..use_cases.characters_chat.get import (
    GetSimpleCharacterInfoUseCaseProtocol,
    GetSimpleCharacterInfoUseCase,
)


def __get_character_chat_repository(session: AsyncSession = Depends(get_async_session)) -> CharacterChatRepositoryProtocol:
    return CharacterChatRepository(session)


def get_character_chat_service(repository: CharacterChatRepositoryProtocol = Depends(__get_character_chat_repository)) -> CharacterChatServiceProtocol:
    return CharacterChatService(repository)


def get_get_online_characters_use_case(character_chat_service: CharacterChatServiceProtocol = Depends(get_character_chat_service)) -> GetOnlineCharactersUseCaseProtocol:
    return GetOnlineCharactersUseCase(character_chat_service)


def get_get_characters_by_ids_use_case(character_chat_service: CharacterChatServiceProtocol = Depends(get_character_chat_service)) -> GetCharactersByIdsUseCaseProtocol:
    return GetCharactersByIdsUseCase(character_chat_service)


def get_get_simple_character_info_use_case(character_chat_service: CharacterChatServiceProtocol = Depends(get_character_chat_service)) -> GetSimpleCharacterInfoUseCaseProtocol:
    return GetSimpleCharacterInfoUseCase(character_chat_service)
