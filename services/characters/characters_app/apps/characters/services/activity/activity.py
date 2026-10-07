import uuid
from typing import Protocol
from typing_extensions import Self
import logging
from shared.schemas.characters import CharacterUpdateSchema
from ...repositories.activity.activity import CharacterActivityRepositoryProtocol
from ...schemas import (
    CharacterActivityCreateDBSchema,
    CharacterActivityCreateSchema,
    CharacterActivityReadSchema,
    StatusSchema
)
from ..character.characters import UpdateCharacterStatusServiceProtocol
from ...enums import ActionType 

logger = logging.getLogger(__name__)

class CharacterActivityServiceProtocol(Protocol):
    async def create(self: Self, activity: CharacterActivityCreateSchema, character_id: uuid.UUID) -> CharacterActivityReadSchema:
        ...

    async def bulk_create(self: Self, activities: list[CharacterActivityCreateDBSchema]) -> list[CharacterActivityReadSchema]:
        ...

class CharacterActivityService(CharacterActivityServiceProtocol):

    def __init__(self: Self, repository: CharacterActivityRepositoryProtocol):
        self.repository = repository

    async def create(self: Self, activity: CharacterActivityCreateSchema, character_id: uuid.UUID) -> CharacterActivityReadSchema:
        db_activity = CharacterActivityCreateDBSchema(
            character_id=character_id,
            **activity.model_dump()
        )
        return await self.repository.create(db_activity)
    
    async def bulk_create(self: Self, activities: list[CharacterActivityCreateDBSchema]) -> list[CharacterActivityReadSchema]:
        return await self.repository.bulk_create(activities)
    
class CharacterLogoutActivityServiceProtocol(Protocol):
    async def logout_activity(self: Self, characters_ids: list[uuid.UUID]) -> list[CharacterActivityReadSchema]:
        ...

class CharacterActivityWithUpdateStatusServiceProtocol(CharacterActivityServiceProtocol, CharacterLogoutActivityServiceProtocol):
    pass

class CharacterActivityWithUpdateStatusService(CharacterActivityWithUpdateStatusServiceProtocol):
    def __init__(self: Self, activity_service: CharacterActivityServiceProtocol,
                 character_update: UpdateCharacterStatusServiceProtocol):
        self.activity_service = activity_service
        self.character_update = character_update

    async def create(self: Self, activity: CharacterActivityCreateSchema, character_id: uuid.UUID) -> CharacterActivityReadSchema:
        created_activity = await self.activity_service.create(activity, character_id)
        is_online = created_activity.action_type != ActionType.QUIT
        status = StatusSchema(is_online=is_online)
        await self.character_update.update_character_status(character_id, status)
        return created_activity
    
    async def bulk_create(self: Self, activities: list[CharacterActivityCreateDBSchema]) -> list[CharacterActivityReadSchema]:
        return await self.activity_service.bulk_create(activities)

    
    async def logout_activity(self: Self, characters_ids: list[uuid.UUID]) -> list[CharacterActivityReadSchema]:
        activities = [
            CharacterActivityCreateDBSchema(
                action_type=ActionType.LOGOUT,
                character_id=character_id
            )
            for character_id in characters_ids
        ]
        created_activities = await self.bulk_create(activities)
        await self.character_update.bulk_update_characters_to_offline(characters_ids)
        return created_activities
    

class CharacterStatusChangerProtocol(Protocol):
    async def change_status_for_inactive_characters(self: Self) -> bool:
        ...

class CharacterStatusChanger(CharacterStatusChangerProtocol):
    def __init__(self: Self, character_repository: CharacterActivityRepositoryProtocol,
                  character_update: UpdateCharacterStatusServiceProtocol):
        self.character_repository = character_repository
        self.character_update = character_update

    async def change_status_for_inactive_characters(self: Self) -> bool:
        logger.info("Start change status for inactive characters")
        inactive_characters = await self.character_repository.get_inactive_characters_id()
        logger.info(f"Inactive characters detected: {len(inactive_characters.ids)}")
        changed_characters_count = await self.character_update.bulk_update_characters_to_offline(inactive_characters.ids)
        logger.info(f"Inactive characters status changed: {changed_characters_count}")
        return True


class CleanupOldActivityServiceProtocol(Protocol):
    async def cleanup_old_activity(self: Self) -> bool:
        ...

class CleanupOldActivityService(CleanupOldActivityServiceProtocol):
    def __init__(self: Self, repository: CharacterActivityRepositoryProtocol):
        self.repository = repository

    async def cleanup_old_activity(self: Self) -> bool:
        logger.info("Start clean old activity")
        await self.cleanup_old_activity()
        logger.info("Old activity successfully cleaned")
        return True
