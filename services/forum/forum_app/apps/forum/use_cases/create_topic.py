import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.utils.exceptions import PermissionDeniedError
from ....core.use_cases import UseCaseProtocol 
from ..schemas import (
   TopicCreateSchema,
   TopicReadSchema
)
from ..adapters.characters import CharacterServiceClientProtocol
from ..services.topic import TopicServiceProtocol 


class CreateTopicUseCaseProtocol(UseCaseProtocol[TopicReadSchema]):
    async def __call__(self: Self, forum_id: uuid.UUID, topic: TopicCreateSchema, token_data: UserTokenDataReadSchema) -> TopicReadSchema:

        ...


class CreateTopicUseCase(CreateTopicUseCaseProtocol):
    def __init__(self: Self, service: TopicServiceProtocol, character_client: CharacterServiceClientProtocol):
        self.service = service
        self.character_client = character_client

    async def __call__(self: Self, forum_id: uuid.UUID, topic: TopicCreateSchema, token_data: UserTokenDataReadSchema) -> TopicReadSchema:
        if not token_data.is_main:
            raise PermissionDeniedError()
        return await self.service.create(forum_id, topic, token_data.user_id)