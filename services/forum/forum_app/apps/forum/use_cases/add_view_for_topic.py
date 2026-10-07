import uuid
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..services.topic import TopicActivityServiceProtocol 


class AddViewForTopicUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, topic_id: uuid.UUID) -> None:
        ...


class AddViewForTopicUseCase(AddViewForTopicUseCaseProtocol):
    def __init__(self: Self, service: TopicActivityServiceProtocol):
        self.service = service

    async def __call__(self: Self, topic_id: uuid.UUID) -> None:
        await self.service.increment_view(topic_id)
        return None