import uuid
import datetime
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from typing import Iterable, Any, Optional
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException, ModelAlreadyExistsError
from ..schemas import (
    TopicCreateDBSchema, TopicUpdateDBSchema, TopicReadSchema, TopicWithStats, 
    TopicWithStatsPaginateSchema
)
from ..models import Topic, Comment

class TopicRepositoryProtocol(BaseRepositoryImpl[
    Topic,
    TopicReadSchema,
    TopicCreateDBSchema,
    TopicUpdateDBSchema
]):
    async def get_topics_by_forum_with_stats_paginated(
        self: Self, 
        forum_id: uuid.UUID,
        pagination: PaginationSchema,
        search: Optional[str] = None,
        search_by: Iterable[str] = [],
        sorting: Iterable[str] = [],
        user: Any = None,
        policies: list[str] = [],
    ) -> TopicWithStatsPaginateSchema:
        ...

    async def update_name(
            self: Self, id: uuid.UUID, name: str
    ) -> TopicReadSchema:
        ...

    async def increment_views(self: Self, topic_id: uuid.UUID) -> None:
        ...

    async def update_last_comment(
        self: Self,
        topic_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        ...


class TopicRepository(TopicRepositoryProtocol):
    async def get_topics_by_forum_with_stats_paginated(
    self: Self, 
    forum_id: uuid.UUID,
    pagination: PaginationSchema,
    search: Optional[str] = None,
    search_by: Iterable[str] = [],
    sorting: Iterable[str] = [],
    user: Any = None,
    policies: list[str] = [],
) -> TopicWithStatsPaginateSchema:
        if len(policies) == 0:
            return TopicWithStatsPaginateSchema(objects=[], count=0)

        async with self.session as s:
            # Базовый запрос с подсчетом комментариев
            base_stmt = (
                sa.select(
                    self.model_type,
                    sa.func.count(Comment.id).label('comments_count')
                )
                .outerjoin(Comment, self.model_type.id == Comment.topic_id)
                .where(self.model_type.forum_id == forum_id)
                .group_by(self.model_type.id)
            )
            
            # Добавляем поиск если указан
            if search:
                search_where: sa.ColumnElement[Any] = sa.false()
                for sb in search_by:
                    if sb == 'description':  # Пропускаем поиск по description
                        continue
                    column = getattr(self.model_type, sb)
                    # Для ENUM используем точное сравнение
                    if hasattr(column, 'type') and isinstance(column.type, sa.Enum):
                        search_where = sa.or_(search_where, column == search)
                    else:
                        search_where = sa.or_(search_where, column.ilike(f'%{search}%'))
                base_stmt = base_stmt.having(search_where)
            
            # Добавляем сортировку
            if sorting:
                order_by_expr = self.get_order_by_expr(sorting)
                stmt_with_pagination = base_stmt.order_by(*order_by_expr)
            else:
                # Дефолтная сортировка
                stmt_with_pagination = base_stmt.order_by(
                    self.model_type.last_comment_datetime.desc().nulls_last(), 
                    self.model_type.created_at.desc()
                )
            
            # Применяем пагинацию
            stmt_with_pagination = stmt_with_pagination.limit(pagination.limit).offset(pagination.offset)
            
            results = (await s.execute(stmt_with_pagination)).all()
            
            # Преобразуем результаты в TopicWithStats
            topics_with_stats = []
            for result in results:
                # result[0] - объект модели Topic, result[1] - comments_count
                topic_model = result[0]
                comments_count = result[1] or 0
                
                # Преобразуем модель в схему
                topic_schema = self.read_schema_type.model_validate(topic_model, from_attributes=True)

                topic_with_stats = TopicWithStats(
                    topic=topic_schema,
                    comments_count=comments_count
                )
                topics_with_stats.append(topic_with_stats)
            
            # Подсчитываем общее количество для пагинации
            count_stmt = (
                sa.select(sa.func.count(sa.distinct(self.model_type.id)))
                .select_from(self.model_type)
                .outerjoin(Comment, self.model_type.id == Comment.topic_id)
                .where(self.model_type.forum_id == forum_id)
            )
            
            # Применяем поиск к запросу подсчета
            if search:
                search_where: sa.ColumnElement[Any] = sa.false()
                for sb in search_by:
                    if sb == 'description':  # Пропускаем поиск по description
                        continue
                    column = getattr(self.model_type, sb)
                    if hasattr(column, 'type') and isinstance(column.type, sa.Enum):
                        search_where = sa.or_(search_where, column == search)
                    else:
                        search_where = sa.or_(search_where, column.ilike(f'%{search}%'))
                count_stmt = count_stmt.where(search_where)
            
            count = (await s.execute(count_stmt)).scalar_one()
            
            return TopicWithStatsPaginateSchema(count=count, objects=topics_with_stats)



    async def update_name(self: Self, id: uuid.UUID, name: str) -> TopicReadSchema:
        async with self.session as s, s.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == id)
                .values(name=name)
                .returning(self.model_type)
            )
            result = (await s.execute(stmt)).scalar_one_or_none()
            if result is None:
                raise ModelNotFoundException(self.model_type, id)
            return self.read_schema_type.model_validate(result, from_attributes=True)

    async def increment_views(self: Self, topic_id: uuid.UUID) -> None:
        """Увеличить количество просмотров топика на 1 (без возврата данных)"""
        async with self.session as s, s.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == topic_id)
                .values(views=self.model_type.views + 1)
            )
            result = await s.execute(stmt)
            if result.rowcount == 0:
                raise ModelNotFoundException(self.model_type, topic_id)
            
    async def update_last_comment(
        self: Self,
        topic_id: uuid.UUID,
        last_comment_user_id: uuid.UUID,
        last_comment_datetime: datetime.datetime
    ) -> None:
        async with self.session as s, s.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == topic_id)
                .values(
                    last_comment_user_id=last_comment_user_id,
                    last_comment_datetime=last_comment_datetime
                )
            )
            result = await s.execute(stmt)
            
            # Проверяем количество измененных строк
            if result.rowcount == 0:
                raise ModelNotFoundException(self.model_type, topic_id)
            
            return None
