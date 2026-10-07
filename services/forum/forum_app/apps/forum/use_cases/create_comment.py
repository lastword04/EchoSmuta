import uuid
import asyncio
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.files import FileIdsSchema
from ....core.utils.exceptions import PermissionDeniedError
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
   CommentCreateSchema,
   CommentReadDBSchema,
   CommentReadWithCharacterNameSchema
)
from ..adapters.file_storage import FileServiceClientProtocol
from ..adapters.characters import CharacterServiceClientProtocol
from ..services.comments import CommentServiceProtocol 


class CreateCommentUseCaseProtocol(UseCaseProtocol[CommentReadDBSchema]):
    async def __call__(self: Self, forum_id: uuid.UUID, topic_id: uuid.UUID, comment: CommentCreateSchema, token_data: UserTokenDataReadSchema) -> CommentReadDBSchema:
        ...


class CreateCommentUseCase(CreateCommentUseCaseProtocol):
    def __init__(self: Self, service: CommentServiceProtocol,
                 file_client: FileServiceClientProtocol,
                   character_client: CharacterServiceClientProtocol):
        self.service = service
        self.file_client = file_client
        self.character_client = character_client

    async def __call__(self: Self, forum_id: uuid.UUID, topic_id: uuid.UUID, comment: CommentCreateSchema, token_data: UserTokenDataReadSchema) -> CommentReadDBSchema:
        if not token_data.is_main:
            raise PermissionDeniedError()
        
        created_comment = await self.service.create(forum_id, topic_id, comment, token_data.user_id)
        
        async def get_files():
            if created_comment.files:
                ids = FileIdsSchema(ids=[file.id for file in created_comment.files])
                return await self.file_client.get_by_ids(ids)
            return None
        
        files_with_url, character = await asyncio.gather(
            get_files(),
            self.character_client.get_simple_character_by_user(token_data.user_id)
        )
        
        return CommentReadWithCharacterNameSchema(
            **created_comment.model_dump(exclude={'files'}),
            author_character_name=character.name,
            files=files_with_url.files if files_with_url else []
        )