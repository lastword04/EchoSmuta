import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.visibility_notifications import CheckVisibilityNotificationsRepositoryProtocol


class CheckVisibilityNotificationsServiceProtocol(Protocol):
    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        ...

    async def get_notification_receivers_for_target(
        self: Self,
        owner_character_id: uuid.UUID
    ) -> list[uuid.UUID]:
        ...

class CheckVisibilityNotificationsService(CheckVisibilityNotificationsServiceProtocol):
    def __init__(self: Self, repository: CheckVisibilityNotificationsRepositoryProtocol):
        self.repository = repository

    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        return await self.repository.can_visible_notifications(owner_character_id, target_character_id)
    
    async def get_notification_receivers_for_target(
        self: Self,
        owner_character_id: uuid.UUID
    ) -> list[uuid.UUID]:
        return await self.repository.get_notification_receivers_for_target(owner_character_id)