from fastapi import Depends
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..services.activity.activity import CharacterActivityServiceProtocol
from ..services.game.game import CharacterGameServiceProtocol, CharacterGameService
from ..use_cases.game.play import CharacterJoinToGameUseCaseProtocol, CharacterJoinToGameUseCase
from ..use_cases.game.play_main import CharacterJoinMainToGameUseCaseProtocol, CharacterJoinMainToGameUseCase
from ..use_cases.game.quit import CharacterQuitFromGameUseCaseProtocol, CharacterQuitFromGameUseCase
from ..use_cases.game.quit_all import CharacterQuitAllFromGameUseCaseProtocol, CharacterQuitAllFromGameUseCase
from .activity import get_character_activity_with_status_service
from .valid import __get_character_repository


def get_character_game_service(character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
        character_activity: CharacterActivityServiceProtocol = Depends(get_character_activity_with_status_service)
        ) -> CharacterGameServiceProtocol:
    return CharacterGameService(repository=character_repository, character_activity=character_activity)


def get_character_join_to_game_use_case(join_to_game_service: CharacterGameServiceProtocol = Depends(get_character_game_service)) -> CharacterJoinToGameUseCaseProtocol:
    return CharacterJoinToGameUseCase(service=join_to_game_service)


def get_character_join_main_to_game_use_case(join_to_game_service: CharacterGameServiceProtocol = Depends(get_character_game_service)) -> CharacterJoinMainToGameUseCaseProtocol:
    return CharacterJoinMainToGameUseCase(service=join_to_game_service)


def get_character_quit_from_game_use_case(quit_from_game_service: CharacterGameServiceProtocol = Depends(get_character_game_service)) -> CharacterQuitFromGameUseCaseProtocol:
    return CharacterQuitFromGameUseCase(service=quit_from_game_service)


def get_character_quit_all_from_game_use_case(quit_from_game_service: CharacterGameServiceProtocol = Depends(get_character_game_service)) -> CharacterQuitAllFromGameUseCaseProtocol:
    return CharacterQuitAllFromGameUseCase(service=quit_from_game_service)
