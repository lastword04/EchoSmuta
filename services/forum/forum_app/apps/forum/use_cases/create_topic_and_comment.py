import uuid
import asyncio
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.files import FileIdsSchema
from ....core.utils.exceptions import PermissionDeniedError
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
    TopicReadWithCharacterNameSchema,
    CommentReadWithCharacterNameSchema,
    TopicCommentCreateSchema,
    TopicCommentReadSchema
)
from ..adapters.file_storage import FileServiceClientProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..services.topic_comments import TopicCommentServiceProtocol 


class CreateTopicAndCommentUseCaseProtocol(UseCaseProtocol[TopicCommentReadSchema]):
    async def __call__(self: Self, forum_id: uuid.UUID, data: TopicCommentCreateSchema, token_data: UserTokenDataReadSchema) -> TopicCommentReadSchema:
        ...


class CreateTopicAndCommentUseCase(CreateTopicAndCommentUseCaseProtocol):
    def __init__(self: Self, service: TopicCommentServiceProtocol,
                 file_client: FileServiceClientProtocol,
                  character_client: CharacterServiceClientProtocol):
        self.service = service
        self.file_client = file_client
        self.character_client = character_client

    async def __call__(self: Self, forum_id: uuid.UUID, data: TopicCommentCreateSchema, token_data: UserTokenDataReadSchema) -> TopicCommentReadSchema:
        if not token_data.is_main:
            raise PermissionDeniedError()
        created_data = await self.service.create(forum_id, data, token_data.user_id)
        created_comment = created_data.comment

        async def get_files():
            if created_comment.files:
                ids = FileIdsSchema(ids=[file.id for file in created_comment.files])
                return await self.file_client.get_by_ids(ids)
            return None
        
        files_with_url, character = await asyncio.gather(
            get_files(),
            self.character_client.get_simple_character_by_user(token_data.user_id)
        )
        
        topic_read = TopicReadWithCharacterNameSchema(
            **created_data.topic.model_dump(),
            author_character_name=character.name
        )
        comment_read = CommentReadWithCharacterNameSchema(
            **created_data.comment.model_dump(exclude={'files'}),
            author_character_name=character.name,
            files=files_with_url.files if files_with_url else []
        )
        
        return TopicCommentReadSchema(
            topic=topic_read,
            comment=comment_read
        )