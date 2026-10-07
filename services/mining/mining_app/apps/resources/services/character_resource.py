import uuid
from typing import Protocol, Self

from ..repositories.character_resource import CharacterResourceRepositoryProtocol
from ..schemas import CharacterResourceReadSchema


class CharacterResourceServiceProtocol(Protocol):
    async def increment_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        increment: int
    ) -> bool:
        ...

    async def decrement_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        decrement: int
    ) -> bool:
        ...

    async def get_by_character_and_resource(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str
    ) -> CharacterResourceReadSchema | None:
        ...

class CharacterResourceService(CharacterResourceServiceProtocol):
    def __init__(self: Self, repository: CharacterResourceRepositoryProtocol):
        self.repository = repository

    async def increment_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        increment: int
    ) -> bool:
        return await self.repository.increment_amount(character_id, resource_slug, increment)

    async def decrement_amount(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str,
        decrement: int
    ) -> bool:
        return await self.repository.decrement_amount(character_id, resource_slug, decrement)

    async def get_by_character_and_resource(
        self: Self,
        character_id: uuid.UUID,
        resource_slug: str
    ) -> CharacterResourceReadSchema | None:
        return await self.repository.get_by_character_and_resource(character_id, resource_slug)