import uuid
from typing import Protocol
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema, CharacterListIds, CharacterSimpleReadSchema
from .....core.utils.exceptions import ModelNotFoundException
from ...models import Character
from ...repositories.character.characters import CharacterRepositoryProtocol
from ...enums import ActionType
from ...schemas import CharacterActivityCreateSchema
from ..activity.activity import CharacterActivityWithUpdateStatusServiceProtocol

class CharacterGameServiceProtocol(Protocol):
    async def join(self: Self, user_id: uuid.UUID, character_id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def join_main(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def quit(self: Self, character_id: uuid.UUID, user_token_id: uuid.UUID) -> CharacterReadSchema:
        ...
    
    async def quit_all(self: Self, user_token_id: uuid.UUID) -> CharacterListIds:
        ...


class CharacterGameService(CharacterGameServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol,
                 character_activity: CharacterActivityWithUpdateStatusServiceProtocol):
        self.repository = repository
        self.character_activity = character_activity

    async def join(self: Self, user_id: uuid.UUID, character_id: uuid.UUID) -> CharacterReadSchema:
        character = await self.repository.get(character_id)
        if character.user_id != user_id:
            raise ModelNotFoundException(Character, character_id)
        activity = CharacterActivityCreateSchema(
            action_type=ActionType.PLAY
        )
        await self.character_activity.create(activity, character_id)
        return character
    
    async def join_main(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        character = await self.repository.get_main_by_user_id(user_id)
        activity = CharacterActivityCreateSchema(
            action_type=ActionType.PLAY
        )
        await self.character_activity.create(activity, character.id)
        return character
    
    async def quit(self: Self, character_id: uuid.UUID, user_token_id: uuid.UUID) -> CharacterReadSchema:
        character = await self.repository.get(character_id)
        if character.user_id != user_token_id:
            raise ModelNotFoundException(Character, character_id)
        activity = CharacterActivityCreateSchema(
            action_type=ActionType.QUIT
        )
        await self.character_activity.create(activity, character_id)
        return character
    
    async def quit_all(self: Self, user_token_id: uuid.UUID) -> CharacterListIds:
        all_characters = await self.repository.get_all_simple_by_user_id(user_token_id)
        characters_ids = [character.id for character in all_characters]
        await self.character_activity.logout_activity(characters_ids)
        return CharacterListIds(ids=characters_ids)