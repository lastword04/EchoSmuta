import uuid
import sqlalchemy as sa
from typing import Iterable, Any, Optional, Sequence
from typing_extensions import Self
from shared.schemas.base import PaginationSchema
from shared.schemas.characters import (
    PaginationCharacterSimpleInfoReadSchema, CharacterSimpleInfoReadSchema,
    CharacterMiningStats
)
from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import Character
from ...schemas import CharacterCreateDBSchema, CharacterUpdateDBSchema
from .....core.utils.exceptions import ModelNotFoundException
 
class CharacterChatRepositoryProtocol(BaseRepositoryImpl[
    Character,
    CharacterSimpleInfoReadSchema,
    CharacterCreateDBSchema,
    CharacterUpdateDBSchema
]):
    async def paginate_online_active(
        self: Self,
        search: str,
        search_by: Iterable[str],
        sorting: Iterable[str],
        pagination: PaginationSchema,
        user: Any,
        policies: list[str],
        location_slug: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> PaginationCharacterSimpleInfoReadSchema:
        ...

    async def get_by_ids(self: Self, ids: Sequence[uuid.UUID], is_online: Optional[bool] = None) -> list[CharacterSimpleInfoReadSchema]:
        ...

    async def get(self: Self, id: uuid.UUID) -> CharacterMiningStats:
        ...


class CharacterChatRepository(CharacterChatRepositoryProtocol):
    async def paginate_online_active(
    self: Self,
    search: str,
    search_by: Iterable[str],
    sorting: Iterable[str],
    pagination: PaginationSchema,
    user: Any,
    policies: list[str],
    location_slug: Optional[str] = None,
    room_id: Optional[str] = None,
) -> PaginationCharacterSimpleInfoReadSchema:
        if len(policies) == 0:
            return PaginationCharacterSimpleInfoReadSchema(objects=[], count=0)
        async with self.session as s:
            statement = self._get_need_fields()

            # Добавляем фильтрацию по is_online и is_active
            statement = statement.where(
                sa.and_(
                    self.model_type.is_online == True,
                    self.model_type.is_active == True
                )
            )

            # Фильтрация по «пространству»:
            #   - room_id = 'house:uuid'  → персонажи внутри конкретного дома
            #   - room_id = 'inn:inside'  → персонажи внутри номеров гостиницы
            #   - иначе                   → как раньше, по location_slug
            #
            # Для inn:inside проверка rest_state='inside' достаточна: sync_on_location_change
            # и _cleanup_expired_rental гарантируют сброс при уходе из локации гостиницы.
            if room_id is not None:
                if room_id.startswith("house:"):
                    try:
                        house_uuid = uuid.UUID(room_id.split(":", 1)[1])
                        statement = statement.where(self.model_type.current_house_id == house_uuid)
                    except (ValueError, IndexError):
                        statement = statement.where(sa.false())
                elif room_id == "inn:inside":
                    statement = statement.where(self.model_type.rest_state == "inside")
                else:
                    # Обычная локация. current_room_id IS NULL означает «в общем
                    # пространстве локации», а не в изолированной комнате
                    # (дом/номер). Так «снаружи гостиницы» не показывает тех,
                    # кто уже в номере, а «улица ЧД» — тех, кто в доме.
                    statement = statement.where(
                        self.model_type.location_slug == room_id,
                        self.model_type.current_room_id.is_(None),
                    )
            elif location_slug is not None:
                statement = statement.where(
                    self.model_type.location_slug == location_slug,
                    self.model_type.current_room_id.is_(None),
                )

            if search:
                search_where: sa.ColumnElement[Any] = sa.false()
                for sb in search_by:
                    column = getattr(self.model_type, sb)
                    # Для ENUM используем точное сравнение
                    if hasattr(column, 'type') and isinstance(column.type, sa.Enum):
                        search_where = sa.or_(search_where, column == search)
                    else:
                        search_where = sa.or_(search_where, column.ilike(f'%{search}%'))
                statement = statement.where(search_where)

            order_by_expr = self.get_order_by_expr(sorting)
            result = await s.execute(
                statement.limit(pagination.limit).offset(pagination.offset).order_by(*order_by_expr)
            )
            rows = result.fetchall()

            # Преобразуем строки в словари
            objects = [
                self.read_schema_type.model_validate({
                    'id': row.id,
                    'name': row.name,
                    'is_male': row.is_male,
                    'race': row.race,
                    'level': row.level,
                    'is_online': row.is_online,
                    'location_slug': row.location_slug,
                    'current_room_id': row.current_room_id,
                })
                for row in rows
            ]

            count_statement = statement.with_only_columns(sa.func.count(self.model_type.id))
            count = (await s.execute(count_statement)).scalar_one()
            return PaginationCharacterSimpleInfoReadSchema(count=count, objects=objects)
    
    async def get_by_ids(self: Self, ids: Sequence[uuid.UUID], is_online: Optional[bool] = None) -> list[CharacterSimpleInfoReadSchema]:
        async with self.session as s:
            statement = self._get_need_fields().where(self.model_type.id.in_(ids), self.model_type.is_active)
            if is_online:
                statement = statement.where(
                    self.model_type.is_online == is_online
                )
            models = (await s.execute(statement)).mappings().all()
            return [self.read_schema_type.model_validate(model) for model in models]

    async def get(self: Self, id: uuid.UUID) -> CharacterMiningStats:
        async with self.session as s:
            statement = self._get_mining_stats().where(self.model_type.id == id, self.model_type.is_active)
            result = await s.execute(statement)
            row = result.mappings().first()

            if not row:
                raise ModelNotFoundException(self.model_type, id)
            
            return CharacterMiningStats.model_validate(row)


    def _get_need_fields(self: Self) -> sa.Select:
        return (
            sa.select(
                self.model_type.id, self.model_type.name, self.model_type.is_male,
                self.model_type.race, self.model_type.level, self.model_type.is_online, 
                self.model_type.location_slug,
                self.model_type.current_room_id,
            )
        )
    
    def _get_mining_stats(self: Self) -> sa.Select:
        return (
            sa.select(
                self.model_type.id, self.model_type.name, self.model_type.level, self.model_type.is_online, 
                self.model_type.location_slug, self.model_type.health, self.model_type.max_health,
                self.model_type.tiredness,
                self.model_type.power.label("strength"),
                self.model_type.agility,
                self.model_type.lucky.label("luck"),
            )
        )
