import asyncio
import logging
from typing_extensions import Self
from shared.schemas.characters import UserListids
from shared.schemas.files import FileIdsSchema
from shared.schemas.base import PaginationSchema
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
    CommentReadDBPaginateSchema,
    CommentReadWithCharacterNamePaginateSchema,
    CommentReadWithCharacterNameSchema
)
from ..services.comments import CommentServiceProtocol 
from ..adapters.characters import CharacterServiceClientProtocol
from ..adapters.file_storage import FileServiceClientProtocol
import uuid

logger = logging.getLogger(__name__)

class GetCommentsByTopicWithCharacterNamesUseCaseProtocol(UseCaseProtocol[CommentReadWithCharacterNamePaginateSchema]):
    async def __call__(
        self: Self, 
        topic_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> CommentReadWithCharacterNamePaginateSchema:
        ...


class GetCommentsByTopicWithCharacterNamesUseCase(GetCommentsByTopicWithCharacterNamesUseCaseProtocol):
    def __init__(self: Self, 
                 service: CommentServiceProtocol,
                 file_client: FileServiceClientProtocol,
                 character_client: CharacterServiceClientProtocol):
        self.service = service
        self.file_client = file_client
        self.character_client = character_client

    async def __call__(
        self: Self, 
        topic_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> CommentReadWithCharacterNamePaginateSchema:
        logger.info(f"Starting get comments with character names for topic {topic_id}, limit={limit}, offset={offset}")
        
        paginate_schema = PaginationSchema(limit=limit, offset=offset)
        comments_paginated: CommentReadDBPaginateSchema = await self.service.paginate(
            topic_id=topic_id,
            paginate=paginate_schema
        )
        
        if not comments_paginated.objects:
            logger.info("No comments found, returning empty result")
            return CommentReadWithCharacterNamePaginateSchema(
                count=comments_paginated.count,
                objects=[]
            )
        
        # Собираем уникальные ID авторов комментариев
        users_ids = {
            comment.author_user_id 
            for comment in comments_paginated.objects
        }
        logger.debug(f"Found {len(users_ids)} unique character IDs to fetch")
        
        # Собираем уникальные ID файлов
        files_ids = {
            file.id
            for comment in comments_paginated.objects
            for file in comment.files
        }
        logger.debug(f"Found {len(files_ids)} unique file IDs to fetch")

        # Параллельно получаем имена персонажей и информацию о файлах
        characters_map = {}
        files_map = {}
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        
        if users_ids:
            logger.debug("Creating character fetch task")
            character_task = self.character_client.get_list_simple_characters_by_users(
                UserListids(ids=list(users_ids))
            )
            tasks.append(character_task)
        else:
            character_task = None
            logger.debug("No character IDs to fetch")
        
        if files_ids:
            logger.debug("Creating file fetch task")
            files_task = self.file_client.get_by_ids(
                FileIdsSchema(ids=list(files_ids))
            )
            tasks.append(files_task)
        else:
            files_task = None
            logger.debug("No file IDs to fetch")
        
        # Выполняем все задачи параллельно
        if tasks:
            logger.info(f"Starting parallel fetch of external data: {len(tasks)} tasks")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            result_index = 0
            if character_task:
                character_result = results[result_index]
                if isinstance(character_result, Exception):
                    logger.error(f"Failed to fetch character data: {character_result}", exc_info=True)
                    characters_map = {}
                else:
                    characters_map = {
                        char.user_id: char.name 
                        for char in character_result.characters
                    }
                    logger.debug(f"Successfully fetched {len(characters_map)} character names")
                result_index += 1
            
            if files_task:
                files_result = results[result_index]
                if isinstance(files_result, Exception):
                    logger.error(f"Failed to fetch file data: {files_result}", exc_info=True)
                    files_map = {}
                else:
                    files_map = {
                        file.id: file 
                        for file in files_result.files
                    }
                    logger.debug(f"Successfully fetched {len(files_map)} file details")
        else:
            logger.info("No external data to fetch, skipping parallel requests")
        
        # Преобразуем комментарии, добавляя имена авторов и файлы
        converted_objects = []
        for comment in comments_paginated.objects:
            author_name = characters_map.get(comment.author_user_id)
            
            files = [
                files_map[file.id] 
                for file in comment.files 
                if file.id in files_map
            ] if comment.files else []
            
            # Создаем новую схему с именем автора
            comment_with_name = CommentReadWithCharacterNameSchema(
                id=comment.id,
                topic_id=comment.topic_id,
                text=comment.text,
                author_user_id=comment.author_user_id,
                author_character_name=author_name,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                files=files,
            )
            
            converted_objects.append(comment_with_name)
        
        # Создаем финальную пагинированную схему
        return CommentReadWithCharacterNamePaginateSchema(
            count=comments_paginated.count,
            objects=converted_objects
        )