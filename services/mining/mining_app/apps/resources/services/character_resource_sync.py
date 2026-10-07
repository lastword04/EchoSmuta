import uuid
from typing import Protocol

from ..repositories.character_resource_sync import CharacterResourceSyncRepository
from ..schemas import CharacterResourceReadSchema


class CharacterResourceSyncServiceProtocol(Protocol):
    def increment_amount(self, character_id: uuid.UUID, resource_slug: str, increment: int) -> bool: ...
    def decrement_amount(self, character_id: uuid.UUID, resource_slug: str, decrement: int) -> bool: ...
    def get_by_character_and_resource(self, character_id: uuid.UUID, resource_slug: str) -> CharacterResourceReadSchema | None: ...


class CharacterResourceSyncService(CharacterResourceSyncServiceProtocol):
    def __init__(self, repository: CharacterResourceSyncRepository):
        self.repository = repository

    def increment_amount(self, character_id: uuid.UUID, resource_slug: str, increment: int) -> bool:
        return self.repository.increment_amount(character_id, resource_slug, increment)

    def decrement_amount(self, character_id: uuid.UUID, resource_slug: str, decrement: int) -> bool:
        return self.repository.decrement_amount(character_id, resource_slug, decrement)

    def get_by_character_and_resource(self, character_id: uuid.UUID, resource_slug: str) -> CharacterResourceReadSchema | None:
        return self.repository.get_by_character_and_resource(character_id, resource_slug)