import uuid
from typing_extensions import Self
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from typing import Iterable, Any, Optional
from shared.schemas.base import PaginationSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..schemas import (
    CommentCreateDBSchema, CommentUpdateDBSchema, CommentReadDBSchema, 
    CommentReadDBPaginateSchema, CommentReadSchema
)
from ..models import Comment

class CommentRepositoryProtocol(BaseRepositoryImpl[
    Comment,
    CommentReadDBSchema,
    CommentCreateDBSchema,
    CommentUpdateDBSchema
]):
    async def get_comments_by_topic_paginated(
    self: Self,
    topic_id: uuid.UUID,
    pagination: PaginationSchema,
    search: Optional[str] = None,
    search_by: Iterable[str] = ['text'],
    sorting: Iterable[str] = ['created_at'],
    user: Any = None,
    policies: list[str] = [],
) -> CommentReadDBPaginateSchema:
        ...

class CommentRepository(CommentRepositoryProtocol):
    async def get_comments_by_topic_paginated(
    self: Self,
    topic_id: uuid.UUID,
    pagination: PaginationSchema,
    search: Optional[str] = None,
    search_by: Iterable[str] = ['text'],
    sorting: Iterable[str] = ['created_at'],
    user: Any = None,
    policies: list[str] = [],
) -> CommentReadDBPaginateSchema:
        if len(policies) == 0:
            return CommentReadDBPaginateSchema(objects=[], count=0)

        async with self.session as s:
            # Базовый запрос
            base_stmt = (
                sa.select(self.model_type)
                .options(joinedload(self.model_type.files))
                .where(self.model_type.topic_id == topic_id)
            )
            
            # Добавляем поиск если указан
            if search:
                search_where: sa.ColumnElement[Any] = sa.false()
                for sb in search_by:
                    column = getattr(self.model_type, sb)
                    # Для ENUM используем точное сравнение
                    if hasattr(column, 'type') and isinstance(column.type, sa.Enum):
                        search_where = sa.or_(search_where, column == search)
                    else:
                        search_where = sa.or_(search_where, column.ilike(f'%{search}%'))
                base_stmt = base_stmt.where(search_where)
            
            # Добавляем сортировку (сначала старые комментарии)
            if sorting:
                order_by_expr = self.get_order_by_expr(sorting)
                stmt_with_pagination = base_stmt.order_by(*order_by_expr)
            else:
                # Дефолтная сортировка - сначала старые (ASC)
                stmt_with_pagination = base_stmt.order_by(self.model_type.created_at.asc())
            
            # Применяем пагинацию
            stmt_with_pagination = stmt_with_pagination.limit(pagination.limit).offset(pagination.offset)
            
            # Выполняем запрос
            results = (await s.execute(stmt_with_pagination)).unique().scalars().all()
            
            # Преобразуем в схемы
            comments = [CommentReadSchema.model_validate(comment, from_attributes=True) for comment in results]
            
            # Подсчитываем общее количество для пагинации
            count_stmt = (
                sa.select(sa.func.count(self.model_type.id))
                .where(self.model_type.topic_id == topic_id)
            )
            
            # Применяем поиск к запросу подсчета
            if search:
                search_where: sa.ColumnElement[Any] = sa.false()
                for sb in search_by:
                    column = getattr(self.model_type, sb)
                    if hasattr(column, 'type') and isinstance(column.type, sa.Enum):
                        search_where = sa.or_(search_where, column == search)
                    else:
                        search_where = sa.or_(search_where, column.ilike(f'%{search}%'))
                count_stmt = count_stmt.where(search_where)
            
            count = (await s.execute(count_stmt)).scalar_one()
            
            return CommentReadDBPaginateSchema(count=count, objects=comments)