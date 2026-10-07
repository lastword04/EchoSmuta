import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from ....core.utils.exceptions import PermissionDeniedError
from ....core.use_cases import UseCaseProtocol 
from ..adapters.characters import CharacterServiceClientProtocol
from ..services.topic import TopicServiceProtocol 


class DeleteTopicUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, topic_id: uuid.UUID, token_data: UserTokenDataReadSchema) -> None:

        ...


class DeleteTopicUseCase(DeleteTopicUseCaseProtocol):
    def __init__(self: Self, service: TopicServiceProtocol, character_client: CharacterServiceClientProtocol):
        self.service = service
        self.character_client = character_client

    async def __call__(self: Self, topic_id: uuid.UUID, token_data: UserTokenDataReadSchema) -> None:
        if not token_data.is_main:
            raise PermissionDeniedError()
        await self.service.delete(topic_id, token_data.user_id)
        return None