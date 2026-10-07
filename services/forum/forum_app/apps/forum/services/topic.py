import uuid
from datetime import datetime, timezone
from typing import Protocol
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from ....core.utils.exceptions import PermissionDeniedError
from ..repositories.topic import TopicRepositoryProtocol
from .forum import UpdateLastCommentsServiceProtocol
from ..schemas import (
    TopicWithStatsPaginateSchema,
    TopicCreateDBSchema,
    TopicUpdateDBSchema,
    TopicCreateSchema,
    TopicUpdateSchema,
    TopicReadSchema
)

class TopicServiceProtocol(Protocol):
    async def get_paginated(self: Self, paginate: PaginationSchema, forum_id: uuid.UUID) -> TopicWithStatsPaginateSchema:
        ...

    async def create(self: Self, forum_id: uuid.UUID, data: TopicCreateSchema, creator_user_id: uuid.UUID) -> TopicReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: TopicUpdateDBSchema, user_id: uuid.UUID) -> TopicReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID, user_id: uuid.UUID) -> None:
        ...

class TopicService(TopicServiceProtocol):
    def __init__(self: Self, repository: TopicRepositoryProtocol, forum_service: UpdateLastCommentsServiceProtocol):
        self.repository = repository
        self.forum_service = forum_service

    async def get_paginated(self: Self, paginate: PaginationSchema, forum_id: uuid.UUID) -> TopicWithStatsPaginateSchema:

        return await self.repository.get_topics_by_forum_with_stats_paginated(forum_id, paginate, policies=['view_forum'])

    async def create(self: Self, forum_id: uuid.UUID, data: TopicCreateSchema, creator_user_id: uuid.UUID) -> TopicReadSchema:
        db_schema = TopicCreateDBSchema(**data.model_dump(), author_user_id=creator_user_id,
                                        last_comment_user_id=creator_user_id,
                                        last_comment_datetime=datetime.now(timezone.utc),
                                        forum_id=forum_id)
        created_topic = await self.repository.create(db_schema)
        await self.forum_service.update_last_comment(
            forum_id=created_topic.forum_id,
            last_comment_user_id=creator_user_id,
            last_comment_datetime=created_topic.created_at
        )
        return created_topic

    async def update(self: Self, id: uuid.UUID, data: TopicUpdateSchema,  user_id: uuid.UUID) -> TopicReadSchema:
        topic = await self.repository.get(id)
        if topic.author_user_id != user_id:
            raise PermissionDeniedError()
        return await self.repository.update_name(id, data.name)

    async def delete(self: Self, id: uuid.UUID, user_id: uuid.UUID) -> None:
        topic = await self.repository.get(id)
        if topic.author_user_id != user_id:
            raise PermissionDeniedError()
        await self.repository.delete(id)


class TopicActivityServiceProtocol(Protocol):
    async def increment_view(self: Self) -> None:
        ...


class TopicActivityService(TopicActivityServiceProtocol):

    def __init__(self: Self, repository: TopicRepositoryProtocol):
        self.repository = repository

    async def increment_view(self: Self, topic_id: uuid.UUID) -> None:
        await self.repository.increment_views(topic_id)
        return None
    

class UpdateLastCommentsForTopicServiceProtocol(Protocol):
    async def update_last_comment(
        self: Self,
        topic_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime
    ) -> None:
        ...


class UpdateLastCommentsForTopicService(UpdateLastCommentsForTopicServiceProtocol):
    def __init__(self: Self, repository: TopicRepositoryProtocol):
        self.repository = repository

    async def update_last_comment(
        self: Self,
        topic_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime
    ) -> None:
        return await self.repository.update_last_comment(
            topic_id, last_comment_user_id, last_comment_datetime
        )