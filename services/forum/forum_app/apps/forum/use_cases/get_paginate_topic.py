from typing_extensions import Self
from shared.schemas.characters import UserListids
from shared.schemas.base import PaginationSchema
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
    TopicWithStatsPaginateSchema,
    TopicWithStatsAndCharacterNamesPaginateSchema,
    TopicWithStatsAndCharacterNames,
    TopicReadWithCharacterNameSchema
)
from ..services.topic import TopicServiceProtocol 
from ..adapters.characters import CharacterServiceClientProtocol
import uuid


class GetTopicsByForumWithStatsUseCaseProtocol(UseCaseProtocol[TopicWithStatsAndCharacterNamesPaginateSchema]):
    async def __call__(
        self: Self, 
        forum_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> TopicWithStatsAndCharacterNamesPaginateSchema:
        ...


class GetTopicsByForumWithStatsUseCase(GetTopicsByForumWithStatsUseCaseProtocol):
    def __init__(self: Self, service: TopicServiceProtocol,
                 character_client: CharacterServiceClientProtocol):
        self.service = service
        self.character_client = character_client

    async def __call__(
        self: Self, 
        forum_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> TopicWithStatsAndCharacterNamesPaginateSchema:
        paginate_schema = PaginationSchema(limit=limit, offset=offset)
        # Получаем топики со статистикой с пагинацией
        topics_stats_paginated: TopicWithStatsPaginateSchema = await self.service.get_paginated(
            forum_id=forum_id,
            paginate=paginate_schema
        )
        
        # Собираем уникальные ID персонажей (авторов и последних комментаторов)
        users_ids = set()
        for topic_stats in topics_stats_paginated.objects:
            # ID автора топика
            users_ids.add(topic_stats.topic.author_user_id)
            # ID автора последнего комментария
            if topic_stats.topic.last_comment_user_id:
                users_ids.add(topic_stats.topic.last_comment_user_id)
        
        users_ids = list(users_ids)
        
        # Получаем данные персонажей
        characters_map = {}
        if users_ids:
            req_characters = await self.character_client.get_list_simple_characters_by_users(
                UserListids(ids=users_ids)
            )
            characters = req_characters.characters
            # Создаем мапу id -> name для быстрого поиска
            characters_map = {char.user_id: char.name for char in characters}
        # Преобразуем TopicWithStats в TopicWithStatsAndCharacterNames
        converted_objects = []
        for topic_stats in topics_stats_paginated.objects:
            # Получаем имена персонажей
            author_character_name = characters_map.get(
                topic_stats.topic.author_user_id
            )
            last_comment_character_name = None
            if topic_stats.topic.last_comment_user_id:
                last_comment_character_name = characters_map.get(
                    topic_stats.topic.last_comment_user_id
                )
            
            # Создаем TopicReadWithCharacterNameSchema из TopicReadSchema
            topic_dict = topic_stats.topic.model_dump()
            topic_dict['author_character_name'] = author_character_name
            topic_dict['last_comment_character_name'] = last_comment_character_name
            
            topic_with_character_names = TopicReadWithCharacterNameSchema(**topic_dict)
            
            # Создаем финальную схему
            topic_with_stats_and_names = TopicWithStatsAndCharacterNames(
                topic=topic_with_character_names,
                comments_count=topic_stats.comments_count
            )
            
            converted_objects.append(topic_with_stats_and_names)
        
        # Создаем финальную пагинированную схему
        return TopicWithStatsAndCharacterNamesPaginateSchema(
            count=topics_stats_paginated.count,
            objects=converted_objects
        )