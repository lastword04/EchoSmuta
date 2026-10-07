from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from ...settings import Settings, get_settings
from .repositories.forum import ForumRepositoryProtocol, ForumRepository
from .repositories.topic import TopicRepositoryProtocol, TopicRepository
from .repositories.comments import CommentRepositoryProtocol, CommentRepository
from .repositories.files import FileRepositoryProtocol, FileRepository
from .services.files import FileServiceProtocol, FileService
from .services.forum import (
    ForumServiceProtocol, ForumService,
    UpdateLastCommentsServiceProtocol, UpdateLastCommentsService
)
from .services.topic import (
    TopicServiceProtocol, TopicService,
    TopicActivityServiceProtocol, TopicActivityService,
    UpdateLastCommentsForTopicServiceProtocol, UpdateLastCommentsForTopicService
)

from .services.comments import CommentServiceProtocol, CommentService
from .services.topic_comments import (
    TopicCommentServiceProtocol, TopicCommentService
)
from .adapters.file_storage import FileServiceClientProtocol, FileServiceClient
from .adapters.characters import CharacterServiceClientProtocol, CharacterServiceClient
from .use_cases.initialize_forums import InitializeForumUseCaseProtocol, InitializeForumUseCase
from .use_cases.get_all_forums import GetAllForumUseCaseProtocol, GetAllForumUseCase
from .use_cases.get_paginate_topic import GetTopicsByForumWithStatsUseCaseProtocol, GetTopicsByForumWithStatsUseCase
from .use_cases.create_topic import CreateTopicUseCaseProtocol, CreateTopicUseCase
from .use_cases.update_topic import UpdateTopicUseCaseProtocol, UpdateTopicUseCase
from .use_cases.delete_topic import DeleteTopicUseCaseProtocol, DeleteTopicUseCase
from .use_cases.add_view_for_topic import AddViewForTopicUseCaseProtocol, AddViewForTopicUseCase
from .use_cases.create_comment import CreateCommentUseCaseProtocol, CreateCommentUseCase
from .use_cases.get_comments import GetCommentsByTopicWithCharacterNamesUseCaseProtocol, GetCommentsByTopicWithCharacterNamesUseCase
from .use_cases.auth_forum import (
    AuthForumUseCaseProtocol, AuthForumUseCase
)
from .use_cases.create_topic_and_comment import (
    CreateTopicAndCommentUseCaseProtocol, CreateTopicAndCommentUseCase
)


def __get_forum_repository_session(session: AsyncSession) -> ForumRepositoryProtocol:
    return ForumRepository(session)

def get_forum_service_session(session: AsyncSession) -> ForumServiceProtocol:
    repository = __get_forum_repository_session(session)
    return ForumService(repository)

def get_initialize_forum_use_case(session: AsyncSession) -> InitializeForumUseCaseProtocol:
    service = get_forum_service_session(session)
    return InitializeForumUseCase(service)







def __get_forum_repository(session: AsyncSession = Depends(get_async_session)) -> ForumRepositoryProtocol:
    """
    Функция для получения репозитория форумов.
    """
    return ForumRepository(session=session)


def get_forum_service(repository: ForumRepositoryProtocol = Depends(__get_forum_repository)) -> ForumServiceProtocol:
    """
    Функция для получения сервиса форумов.
    """
    return ForumService(repository=repository)

def get_update_last_comment_for_forum_service(repository: ForumRepositoryProtocol = Depends(__get_forum_repository)) -> UpdateLastCommentsServiceProtocol:
    return UpdateLastCommentsService(repository=repository)

def get_character_service_client(settings: Settings = Depends(get_settings)) -> CharacterServiceClientProtocol:
    """
    Функция для получения клиента сервиса персонажей.
    """
    return CharacterServiceClient(base_url=settings.character_service_app.base_url)

def get_file_service_client(settings: Settings = Depends(get_settings)) -> FileServiceClientProtocol:
    """
    Функция для получения клиента сервиса файлов.
    """
    return FileServiceClient(base_url=settings.file_service_app.base_url)

def get_all_forum_use_case(service: ForumServiceProtocol = Depends(get_forum_service),
                            character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)) -> GetAllForumUseCaseProtocol:
     """
     Функция для получения use case получения всех форумов с персонажами.
     """
     return GetAllForumUseCase(service=service, character_client=character_client)

def __get_topic_repository(session: AsyncSession = Depends(get_async_session)) -> TopicRepositoryProtocol:
    return TopicRepository(session)

def get_topic_service(repository: TopicRepositoryProtocol = Depends(__get_topic_repository),
                      forum_service: UpdateLastCommentsServiceProtocol = Depends(get_update_last_comment_for_forum_service)) -> TopicServiceProtocol:
    """
    Функция для получения сервиса тем.
    """
    return TopicService(repository=repository, forum_service=forum_service)

def get_topics_by_forum_with_stats_use_case(
    service: TopicServiceProtocol = Depends(get_topic_service),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> GetTopicsByForumWithStatsUseCaseProtocol:
    """
    Функция для получения use case получения топиков по форуму с персонажами.
    """
    return GetTopicsByForumWithStatsUseCase(service=service, character_client=character_client)

def get_create_topic_use_case(service: TopicServiceProtocol = Depends(get_topic_service),
                               character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)) -> CreateTopicUseCaseProtocol:
    """
    Функция для получения use case создания темы.
    """
    return CreateTopicUseCase(service=service, character_client=character_client)

def get_update_topic_use_case(service: TopicServiceProtocol = Depends(get_topic_service),
                              character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)) -> UpdateTopicUseCaseProtocol:
    return UpdateTopicUseCase(service, character_client)

def get_topic_activity_service(repository: TopicRepositoryProtocol = Depends(__get_topic_repository)) -> TopicActivityServiceProtocol:
    return TopicActivityService(repository)

def get_add_views_use_case(topic_activity: TopicActivityServiceProtocol = Depends(get_topic_activity_service)) -> AddViewForTopicUseCaseProtocol:
    return AddViewForTopicUseCase(topic_activity)

def get_delete_topic_use_case(service: TopicServiceProtocol = Depends(get_topic_service),
                              character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)) -> DeleteTopicUseCaseProtocol:
    return DeleteTopicUseCase(service, character_client)

def get_update_last_comment_for_topic_service(repository: TopicRepositoryProtocol = Depends(__get_topic_repository)) -> UpdateLastCommentsForTopicServiceProtocol:
    return UpdateLastCommentsForTopicService(repository)

def __get_comment_repository(session: AsyncSession = Depends(get_async_session)) -> CommentRepositoryProtocol:
    return CommentRepository(session)

def __get_file_repository(session: AsyncSession = Depends(get_async_session)) -> FileRepositoryProtocol:
    return FileRepository(session)

def get_file_service(repository: FileRepositoryProtocol = Depends(__get_file_repository)) -> FileServiceProtocol:
    return FileService(repository)


def get_comment_service(repository: CommentRepositoryProtocol = Depends(__get_comment_repository),
                        file_service: FileServiceProtocol = Depends(get_file_service),
                        update_forum: UpdateLastCommentsServiceProtocol = Depends(get_update_last_comment_for_forum_service),
                        update_topic: UpdateLastCommentsServiceProtocol = Depends(get_update_last_comment_for_topic_service)) -> CommentServiceProtocol:
    return CommentService(repository, file_service, update_forum, update_topic)


def get_create_comment_use_case(service: CommentServiceProtocol = Depends(get_comment_service),
                                file_client: FileServiceClientProtocol = Depends(get_file_service_client),
                                character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
                                ) -> CreateCommentUseCaseProtocol:
    return CreateCommentUseCase(service, file_client, character_client)

def get_comments_by_topic_with_character_names_use_case(
    service: CommentServiceProtocol = Depends(get_comment_service),
    file_client: FileServiceClientProtocol = Depends(get_file_service_client),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> GetCommentsByTopicWithCharacterNamesUseCaseProtocol:
    return GetCommentsByTopicWithCharacterNamesUseCase(service=service, file_client=file_client, character_client=character_client)


def get_auth_forum_use_case(character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)) -> AuthForumUseCaseProtocol:
    return AuthForumUseCase(character_client=character_client)


def get_comment_and_topic_service(
    comment_service: CommentServiceProtocol = Depends(get_comment_service),
    topic_service: TopicServiceProtocol = Depends(get_topic_service)
) -> TopicCommentServiceProtocol:
    return TopicCommentService(comment_service=comment_service, topic_service=topic_service)

def get_create_comment_and_topic_use_case(
    service: TopicCommentServiceProtocol = Depends(get_comment_and_topic_service),
    file_client: FileServiceClientProtocol = Depends(get_file_service_client),
    character_client: CharacterServiceClientProtocol = Depends(get_character_service_client)
) -> CreateTopicAndCommentUseCaseProtocol:
    return CreateTopicAndCommentUseCase(service=service, file_client=file_client, character_client=character_client)