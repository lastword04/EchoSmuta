import uuid
import datetime
import sqlalchemy as sa
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException
from ..schemas import ForumCreateDBSchema, ForumUpdateDBSchema, ForumReadSchema, ForumWithStats
from ..models import Forum, Topic, Comment

class ForumRepositoryProtocol(BaseRepositoryImpl[
    Forum,
    ForumReadSchema,
    ForumCreateDBSchema,
    ForumUpdateDBSchema
]):
    async def get_all_forums_with_stats(self: Self) -> list[ForumWithStats]:
        ...

    async def update_last_comment(
        self: Self,
        forum_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        ...


class ForumRepository(ForumRepositoryProtocol):
    async def get_all_forums_with_stats(self: Self) -> list[ForumWithStats]:
        async with self.session as s:
            stmt = (
                sa.select(
                    self.model_type,
                    sa.func.count(sa.distinct(Topic.id)).label('topics_count'),
                    sa.func.count(Comment.id).label('comments_count')
                )
                .outerjoin(Topic, self.model_type.id == Topic.forum_id)
                .outerjoin(Comment, Topic.id == Comment.topic_id)
                .group_by(self.model_type.id)
                .order_by(self.model_type.section, self.model_type.created_at.desc())  # Сортировка по дате создания
            )
            
            results = (await s.execute(stmt)).all()
            
            forums_with_stats: list[ForumWithStats] = []
            for result in results:
                forum, topics_count, comments_count = result
                forums_with_stats.append(
                    ForumWithStats(
                        forum=self.read_schema_type.model_validate(forum, from_attributes=True),
                        comments_count=comments_count,
                        topics_count=topics_count
                    )
                )
            
            return forums_with_stats
    
    async def update_last_comment(
        self: Self,
        forum_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        async with self.session as s, s.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == forum_id)
                .values(
                    last_comment_user_id=last_comment_user_id,
                    last_comment_datetime=last_comment_datetime
                )
            )
            result = await s.execute(stmt)
            
            # Проверяем количество измененных строк
            if result.rowcount == 0:
                raise ModelNotFoundException(self.model_type, forum_id)
            
            return None