import datetime
import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.forum import ForumRepositoryProtocol
from ..schemas import (
    ForumCreateDBSchema,
    ForumUpdateDBSchema,
    ForumReadSchema,
    ForumWithStats
)

class ForumServiceProtocol(Protocol):
    async def get(self: Self, id: uuid.UUID) -> ForumReadSchema:
        ...

    async def create(self: Self, data: ForumCreateDBSchema) -> ForumReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: ForumUpdateDBSchema) -> ForumReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def get_all(self: Self) -> list[ForumReadSchema]:
        ...

    async def bulk_create(self: Self, data: list[ForumCreateDBSchema]) -> list[ForumReadSchema]:
        ...

    async def get_all_with_stats(self: Self) -> list[ForumWithStats]:
        ...


class ForumService(ForumServiceProtocol):
    def __init__(self: Self, repository: ForumRepositoryProtocol):
        self.repository = repository

    async def get(self: Self, id: uuid.UUID) -> ForumReadSchema:
        return await self.repository.get(id)

    async def create(self: Self, data: ForumCreateDBSchema) -> ForumReadSchema:
        return await self.repository.create(data)

    async def update(self: Self, id: uuid.UUID, data: ForumUpdateDBSchema) -> ForumReadSchema:
        return await self.repository.update(id, data)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def get_all(self: Self) -> list[ForumReadSchema]:
        return await self.repository.get_all()

    async def get_all_with_stats(self: Self) -> list[ForumWithStats]:
        return await self.repository.get_all_forums_with_stats()


    async def bulk_create(self: Self, data: list[ForumCreateDBSchema]) -> list[ForumReadSchema]:
        return await self.repository.bulk_create(data)
    
class UpdateLastCommentsServiceProtocol(Protocol):
    async def update_last_comment(
        self: Self,
        forum_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        ...

class UpdateLastCommentsService(UpdateLastCommentsServiceProtocol):
    def __init__(self: Self, repository: ForumRepositoryProtocol):
        self.repository = repository

    async def update_last_comment(
        self: Self,
        forum_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        return await self.repository.update_last_comment(
            forum_id, last_comment_user_id, last_comment_datetime
        )