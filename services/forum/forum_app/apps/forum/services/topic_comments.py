import uuid
from typing import Protocol
from typing_extensions import Self
from .topic import TopicServiceProtocol
from .comments import CommentServiceProtocol
from ..schemas import (
    TopicCommentReadDBSchema,
    TopicCommentCreateSchema,
)

class TopicCommentServiceProtocol(Protocol):
    async def create(self: Self, forum_id: uuid.UUID, data: TopicCommentCreateSchema, user_id: uuid.UUID) -> TopicCommentReadDBSchema:
        ...


class TopicCommentService(TopicCommentServiceProtocol):
    def __init__(self: Self, comment_service: CommentServiceProtocol,
                 topic_service: TopicServiceProtocol) -> None:
        self.comment_service = comment_service
        self.topic_service = topic_service

    async def create(self: Self, forum_id: uuid.UUID, data: TopicCommentCreateSchema, user_id: uuid.UUID) -> TopicCommentReadDBSchema:
        created_topic = await self.topic_service.create(
            forum_id=forum_id,
            data=data.topic,
            creator_user_id=user_id
        )

        created_comment = await self.comment_service.create(
            forum_id=forum_id,
            topic_id=created_topic.id,
            data=data.comment,
            user_id=user_id
        )

        return TopicCommentReadDBSchema(
            topic=created_topic,
            comment=created_comment
        )