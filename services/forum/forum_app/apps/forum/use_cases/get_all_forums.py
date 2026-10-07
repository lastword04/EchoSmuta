from typing_extensions import Self
from shared.schemas.characters import UserListids
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
    ForumWithStats,
    ForumWithStatsAndCharacterNames,
    ForumWithCharacterNameReadSchema
)
from ..services.forum import ForumServiceProtocol 
from ..adapters.characters import CharacterServiceClientProtocol


class GetAllForumUseCaseProtocol(UseCaseProtocol[list[ForumWithStatsAndCharacterNames]]):
    async def __call__(self: Self) -> list[ForumWithStatsAndCharacterNames]:
        ...


class GetAllForumUseCase(GetAllForumUseCaseProtocol):
    def __init__(self: Self, service: ForumServiceProtocol,
                 character_client: CharacterServiceClientProtocol):
        self.service = service
        self.character_client = character_client

    async def __call__(self: Self) -> list[ForumWithStatsAndCharacterNames]:
        # Получаем форумы со статистикой
        forums_stats: list[ForumWithStats] = await self.service.get_all_with_stats()
        
        # Собираем уникальные ID персонажей
        users_ids = list(set(
            forum.forum.last_comment_user_id 
            for forum in forums_stats 
            if forum.forum.last_comment_user_id
        ))
        
        # Получаем данные персонажей
        characters_map = {}
        if users_ids:
            req_characters = await self.character_client.get_list_simple_characters_by_users(
                UserListids(ids=users_ids)
            )
            characters = req_characters.characters
            # Создаем мапу id -> name для быстрого поиска
            characters_map = {char.user_id: char.name for char in characters}
        
        # Преобразуем ForumWithStats в ForumWithStatsAndCharacterNames
        result = []
        for forum_stats in forums_stats:
            # Получаем имя персонажа для последнего комментария
            last_comment_character_name = None
            if forum_stats.forum.last_comment_user_id:
                last_comment_character_name = characters_map.get(
                    forum_stats.forum.last_comment_user_id
                )
            
            # Создаем ForumWithCharacterNameReadSchema из ForumReadSchema
            forum_with_character_name = ForumWithCharacterNameReadSchema(
                **forum_stats.forum.model_dump(),
                last_comment_character_name=last_comment_character_name
            )
            
            # Создаем финальную схему
            forum_with_stats_and_names = ForumWithStatsAndCharacterNames(
                forum=forum_with_character_name,
                comments_count=forum_stats.comments_count,
                topics_count=forum_stats.topics_count,
            )
            
            result.append(forum_with_stats_and_names)
        
        return result