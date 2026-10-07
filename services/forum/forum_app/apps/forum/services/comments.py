import uuid
from datetime import datetime, timezone
from typing import Protocol
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from ..repositories.comments import CommentRepositoryProtocol
from .forum import UpdateLastCommentsServiceProtocol
from .topic import UpdateLastCommentsForTopicService
from .files import FileServiceProtocol
from ..schemas import (
    CommentReadDBSchema,
    CommentCreateDBSchema,
    CommentCreateSchema,
    CommentReadDBPaginateSchema,
    FileCreateSchema,
    CommentReadSchema
)

class CommentServiceProtocol(Protocol):
    async def create(self: Self, forum_id: uuid.UUID, topic_id: uuid.UUID, data: CommentCreateSchema, user_id: uuid.UUID) -> CommentReadSchema:
        ...

    async def paginate(self: Self, paginate: PaginationSchema, topic_id: uuid.UUID) -> CommentReadDBPaginateSchema:
        ...

class CommentService(CommentServiceProtocol):
    def __init__(self: Self, repository: CommentRepositoryProtocol,
                 file_service: FileServiceProtocol,
                 update_forum_service: UpdateLastCommentsServiceProtocol,
                 update_topic_service: UpdateLastCommentsForTopicService):
        self.repository = repository
        self.file_service = file_service
        self.update_forum_service = update_forum_service
        self.update_topic_service = update_topic_service

    async def create(self: Self, forum_id: uuid.UUID, topic_id: uuid.UUID, data: CommentCreateSchema, user_id: uuid.UUID) -> CommentReadDBSchema:
        db_schema = CommentCreateDBSchema(
            **data.model_dump(exclude={'files_ids'}),
            topic_id=topic_id,
            author_user_id=user_id
        )
        created_comment = await self.repository.create(db_schema)
        created_files = await self.file_service.bulk_create(
            [FileCreateSchema(id=file_id, comment_id=created_comment.id) for file_id in data.files_ids ]
        ) if data.files_ids else []
        await self.update_forum_service.update_last_comment(forum_id, last_comment_user_id=user_id,
                                                      last_comment_datetime=datetime.now(timezone.utc)
                                                      )
        await self.update_topic_service.update_last_comment(topic_id, last_comment_user_id=user_id,
                                                      last_comment_datetime=datetime.now(timezone.utc)
                                                      )
        return CommentReadSchema(
            **created_comment.model_dump(),
            files=created_files
        )


    async def paginate(self: Self, paginate: PaginationSchema, topic_id: uuid.UUID) -> CommentReadDBPaginateSchema:
        return await self.repository.get_comments_by_topic_paginated(
            topic_id=topic_id,
            pagination=paginate,
            search_by=['text'],
            sorting=['created_at'],
            policies=['view_comment']
        )
