import uuid
import sqlalchemy as sa
from decimal import Decimal
from typing import Optional, Sequence
from typing_extensions import Self
from datetime import datetime, timezone
from shared.schemas.characters import (
    CharacterReadSchema, CharacterSimpleReadSchema,
    
)
from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import Character
from ...schemas import CharacterCreateDBSchema, CharacterUpdateDBSchema, StatusSchema 
from .....core.utils.exceptions import ModelFieldNotFoundException, ModelNotFoundException

class CharacterRepositoryProtocol(BaseRepositoryImpl[
    Character,
    CharacterReadSchema,
    CharacterCreateDBSchema,
    CharacterUpdateDBSchema
]):
    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        ...

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        ...

    async def get_simple(self: Self, id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...

    async def get_simple_by_ids(self: Self, ids: Sequence[uuid.UUID]) -> list[CharacterSimpleReadSchema]:
        ...

    async def get_any_by_name_or_none(self: Self, name: str) -> Optional[CharacterSimpleReadSchema]:
        """Get a character by name, returning None if not found."""
        ...

    async def get_by_name_or_none(self: Self, name: str) -> Optional[CharacterSimpleReadSchema]:
        ...

    async def get_simple_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...

    async def get_all_simple_by_user_id(self: Self, user_id: uuid.UUID) -> list[CharacterSimpleReadSchema]:
        ... 

    async def count_by_user_id(self: Self, user_id: uuid.UUID) -> int:
        ...

    async def get_main_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def has_detached_characters(self: Self, user_id: uuid.UUID) -> bool:
        ...

    async def get_detached_characters(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        ...

    async def delete_all_detached_characters(self: Self) -> bool:
        ...

    async def get_simple_main_by_user_ids(self: Self, user_ids: Sequence[uuid.UUID]) -> list[CharacterSimpleReadSchema]:
        ...

    async def update_character_status(self: Self, character_id: uuid.UUID, status: StatusSchema) -> CharacterReadSchema:
        ...

    async def bulk_update_characters_to_offline(self: Self, character_ids: list[uuid.UUID]) -> int:
        """Множественное обновление статуса для списка персонажей"""
        ...

    async def get_full_by_name(self: Self, name: str) -> CharacterReadSchema:
        ...

    async def is_online(self: Self, id: uuid.UUID) -> bool:
        ...

    async def update_location_slug_by_character(self: Self, character_id: uuid.UUID, location_slug: str) -> CharacterReadSchema:
        ...

    async def update_tiredness(self: Self, character_id: uuid.UUID, tiredness: float) -> bool:
        ...

    async def update_ducats(self: Self, character_id: uuid.UUID, ducats: Decimal) -> bool:
        ...

    async def get_weight_balance(self: Self, character_id: uuid.UUID) -> dict:
        ...

    async def update_weight(self: Self, character_id: uuid.UUID, weight: float) -> bool:
        ...

    async def update_health(self: Self, character_id: uuid.UUID, health: float) -> bool:
        ...

    async def update_mana(self: Self, character_id: uuid.UUID, mana: float) -> bool:
        ...

    async def get_health_mana(self: Self, character_id: uuid.UUID) -> dict:
        """Получить текущие health, max_health, mana, max_mana, tiredness, max_tiredness"""
        ...

    async def get_all_online(self: Self) -> list[Character]:
        """Получить всех онлайн персонажей"""
        ...

    async def update_equipment_bonuses(self: Self, character_id: uuid.UUID, bonuses: dict) -> Character:
        """Обновить бонусы от экипировки"""
        ...

    async def update_food_cooldown(self: Self, character_id: uuid.UUID, food_cooldown_until: datetime) -> bool:
        ...

    async def update_rest_state(self: Self, character_id: uuid.UUID, rest_state: str) -> bool:
        ...

    async def subtract_ducats(self: Self, character_id: uuid.UUID, amount: Decimal) -> bool:
        ...

    async def update_current_house_id(self: Self, character_id: uuid.UUID, house_id: uuid.UUID | None) -> bool:
        ...

    async def update_current_room_id(self: Self, character_id: uuid.UUID, room_id: str | None) -> bool:
        ...

    async def commit(self) -> None: ...

class CharacterRepository(CharacterRepositoryProtocol):
    async def get_by_name_or_none(self: Self, name: str) -> Optional[CharacterSimpleReadSchema]:
        """Get a character by name, returning None if not found."""
        async with self.session as session:
            stmt = self._get_req_for_simple().where(sa.func.lower(self.model_type.name) == sa.func.lower(name),
                                                    self.model_type.is_active)
            result = await session.execute(stmt)
            row = result.mappings().first()

            if not row:
                return None
            
            return CharacterSimpleReadSchema.model_validate(row)
        
    async def get_any_by_name_or_none(self: Self, name: str) -> Optional[CharacterSimpleReadSchema]:
        """Get a character by name, returning None if not found."""
        async with self.session as session:
            stmt = self._get_req_for_simple().where(sa.func.lower(self.model_type.name) == sa.func.lower(name))
            result = await session.execute(stmt)
            row = result.mappings().first()

            if not row:
                return None
            
            return CharacterSimpleReadSchema.model_validate(row)

    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        """Get a character by name, raising an exception if not found."""
        character = await self.get_by_name_or_none(name)
        if not character:
            raise ModelFieldNotFoundException(self.model_type, "name", name)

        return character

    async def get_full_by_name(self: Self, name: str) -> CharacterReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(sa.func.lower(self.model_type.name) == sa.func.lower(name))
            )

            result = (await session.execute(stmt)).scalar_one_or_none()

            if not result:
                raise ModelFieldNotFoundException(self.model_type, "name", name)

            return self.read_schema_type.model_validate(result, from_attributes=True)

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.user_id == user_id,
                       self.model_type.is_active)
                .order_by(self.model_type.created_at.asc()) 
            )
            models = (await session.execute(stmt)).scalars().all()

            return [self.read_schema_type.model_validate(model, from_attributes=True) for model in models]
        
    async def get_simple(self: Self, id: uuid.UUID) -> CharacterSimpleReadSchema:
        async with self.session as session:
            stmt = self._get_req_for_simple().where(self.model_type.id == id, self.model_type.is_active)
            result = await session.execute(stmt)
            row = result.mappings().first()

            if not row:
                raise ModelFieldNotFoundException(self.model_type, "id", id)
            
            return CharacterSimpleReadSchema.model_validate(row)

    async def get_simple_by_ids(self: Self, ids: Sequence[uuid.UUID]) -> list[CharacterSimpleReadSchema]:
        async with self.session as s:
            statement = self._get_req_for_simple().where(self.model_type.id.in_(ids), self.model_type.is_active)
            models = (await s.execute(statement)).mappings().all()
            return [CharacterSimpleReadSchema.model_validate(model) for model in models]

    async def get_simple_main_by_user_ids(self: Self, user_ids: Sequence[uuid.UUID]) -> list[CharacterSimpleReadSchema]:
        async with self.session as s:
            statement = self._get_req_for_simple().where(self.model_type.user_id.in_(user_ids), self.model_type.is_main, self.model_type.is_active)
            models = (await s.execute(statement)).mappings().all()
            return [CharacterSimpleReadSchema.model_validate(model) for model in models]
        
    async def get_simple_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        async with self.session as session:
            stmt = (
                self._get_req_for_simple().where(self.model_type.user_id == user_id, self.model_type.is_main, self.model_type.is_active)
            )
            result = await session.execute(stmt)
            row = result.mappings().first()

            if not row:
                raise ModelFieldNotFoundException(self.model_type, "user_id", user_id)
            
            return CharacterSimpleReadSchema.model_validate(row)
        
    async def get_all_simple_by_user_id(self: Self, user_id: uuid.UUID) -> list[CharacterSimpleReadSchema]:
        async with self.session as session:
            stmt = (
                self._get_req_for_simple()
                .where(self.model_type.user_id == user_id, 
                       self.model_type.is_active)
                .order_by(self.model_type.created_at.asc()) 
            )
            result = await session.execute(stmt)
            rows = result.mappings().all()

            return [CharacterSimpleReadSchema.model_validate(row) for row in rows]

    async def get_main_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                self.model_type.user_id == user_id,
                self.model_type.is_main,
                self.model_type.is_active
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                raise ModelFieldNotFoundException(self.model_type, "user_id", user_id)

            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def count_by_user_id(self: Self, user_id: uuid.UUID) -> int:
        """Count characters by user ID."""
        async with self.session as session:
            stmt = sa.select(sa.func.count()).select_from(self.model_type).where(
                self.model_type.user_id == user_id,
                self.model_type.is_active
            )
            result = await session.execute(stmt)
            count = result.scalar_one_or_none()
            return count or 0
        
    async def has_detached_characters(self: Self, user_id: uuid.UUID) -> bool:
        """Check if user has detached (scheduled for deletion) characters."""
        async with self.session as session:
            exists_query = sa.exists(
                sa.select(1).select_from(self.model_type).where(
                    self.model_type.user_id == user_id,
                    ~self.model_type.is_active,
                    self.model_type.scheduled_deletion_at > sa.func.now()
                )
            )
            stmt = sa.select(exists_query)
            result = await session.execute(stmt)
            return result.scalar() or False
        
    async def get_detached_characters(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        """Get all detached characters for a user."""
        async with self.session as session:
            stmt = sa.select(self.model_type).where(
                self.model_type.user_id == user_id,
                ~self.model_type.is_active,
                self.model_type.scheduled_deletion_at > sa.func.now()
            ).order_by(self.model_type.created_at.asc())
            result = await session.execute(stmt)
            models = result.scalars().all()

            return [self.read_schema_type.model_validate(model, from_attributes=True) for model in models]
        

    async def delete_all_detached_characters(self: Self) -> bool:
        """Delete all detached characters that are past their scheduled deletion time."""
        async with self.session as session, session.begin():
            stmt = sa.delete(self.model_type).where(
                ~self.model_type.is_active,
                self.model_type.scheduled_deletion_at <= sa.func.now()
            )
            await session.execute(stmt)
            return True

    async def update_character_status(self: Self, character_id: uuid.UUID, status: StatusSchema) -> CharacterReadSchema:
        async with self.session as s, s.begin():
            stmt = (
            sa.update(self.model_type)
            .where(self.model_type.id == character_id)
            .values(status.model_dump())
            .returning(self.model_type)
        )
            model = (await s.execute(stmt)).scalar_one_or_none()
            if model is None:
                raise ModelNotFoundException(self.model_type, character_id)

            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def is_online(self: Self, id: uuid.UUID) -> bool:
        async with self.session as session:
            stmt = sa.select(self.model_type.is_online).where(self.model_type.id == id, 
                                                                self.model_type.is_active == True)
            result = await session.execute(stmt)
            is_online = result.scalar_one_or_none()
            
            if is_online is None:
                raise ModelFieldNotFoundException(self.model_type, "id", id)
            
            return is_online
    
    async def bulk_update_characters_to_offline(self: Self, character_ids: list[uuid.UUID]) -> int:
        """Множественное обновление статуса для списка персонажей"""
        if not character_ids:
            return 0
        
        async with self.session as session:
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id.in_(character_ids))
                .values(
                    is_online=False,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount 
        
    async def update_location_slug_by_character(self: Self, character_id: uuid.UUID, location_slug: str) -> CharacterReadSchema:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(location_slug=location_slug)
                .returning(self.model_type)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                raise ModelNotFoundException(self.model_type, character_id)

            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def update_tiredness(self: Self, character_id: uuid.UUID, tiredness: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(tiredness=tiredness)
            )

            await session.execute(stmt)

            return True
        
    async def update_ducats(self: Self, character_id: uuid.UUID, ducats: Decimal) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(ducats=ducats)
            )

            await session.execute(stmt)

            return True

    async def get_weight_balance(self: Self, character_id: uuid.UUID) -> dict:
        async with self.session as session:
            stmt = sa.select(
                self.model_type.id,
                self.model_type.name,
                self.model_type.level,
                self.model_type.is_online,
                self.model_type.location_slug,
                self.model_type.weight,
                self.model_type.max_weight
            ).where(self.model_type.id == character_id, self.model_type.is_active)
            
            result = await session.execute(stmt)
            row = result.mappings().first()
            
            if not row:
                raise ModelFieldNotFoundException(self.model_type, "id", character_id)
            
            return dict(row)

    async def update_weight(self: Self, character_id: uuid.UUID, weight: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(weight=weight)
            )

            await session.execute(stmt)

            return True

    async def update_health(self: Self, character_id: uuid.UUID, health: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(health=health)
            )
            await session.execute(stmt)
            return True

    async def update_mana(self: Self, character_id: uuid.UUID, mana: float) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(mana=mana)
            )
            await session.execute(stmt)
            return True

    async def get_health_mana(self: Self, character_id: uuid.UUID) -> dict:
        async with self.session as session:
            stmt = (
                sa.select(
                    self.model_type.health,
                    self.model_type.max_health,
                    self.model_type.mana,
                    self.model_type.max_mana,
                    self.model_type.tiredness,
                    self.model_type.max_tiredness
                )
                .where(self.model_type.id == character_id)
            )
            result = await session.execute(stmt)
            row = result.first()
            
            if not row:
                raise ModelNotFoundException(self.model_type, character_id)
            
            return {
                "health": row[0],
                "max_health": row[1],
                "mana": row[2],
                "max_mana": row[3],
                "tiredness": row[4],
                "max_tiredness": row[5]
            }

    def _get_req_for_simple(self: Self) -> sa.Select:
        """Helper method to create a SQLAlchemy select statement for getting a simple character by ID."""
        return (
            sa.select(
                self.model_type.id, 
                self.model_type.name, 
                self.model_type.user_id, 
                self.model_type.is_main,
                self.model_type.is_online, 
                self.model_type.is_active,
                self.model_type.is_banned,
                self.model_type.updated_at, 
                self.model_type.created_at
            )
        )

    async def get_all_online(self: Self) -> list[Character]:
        """Получить всех онлайн персонажей"""
        stmt = (
            sa.select(self.model_type)
            .where(self.model_type.is_online == True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_equipment_bonuses(self: Self, character_id: uuid.UUID, bonuses: dict) -> Character:
        """
        Обновляет equipment_bonuses персонажа.
        
        Args:
            character_id: ID персонажа
            bonuses: Словарь бонусов {"strength_bonus": 5, ...}
        
        Returns:
            Обновлённый Character
        """
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(equipment_bonuses=bonuses)
                .returning(self.model_type)
            )
            
            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                raise ModelNotFoundException(self.model_type, character_id)
            
            return model

    async def update_food_cooldown(self: Self, character_id: uuid.UUID, food_cooldown_until: datetime) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(food_cooldown_until=food_cooldown_until)
            )
            await session.execute(stmt)
            return True

    async def update_rest_state(self: Self, character_id: uuid.UUID, rest_state: str) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(rest_state=rest_state)
            )
            await session.execute(stmt)
            return True

    async def subtract_ducats(self: Self, character_id: uuid.UUID, amount: Decimal) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id, self.model_type.ducats >= amount)
                .values(ducats=self.model_type.ducats - amount)
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def update_current_house_id(self: Self, character_id: uuid.UUID, house_id: uuid.UUID | None) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(current_house_id=house_id)
            )
            await session.execute(stmt)
            return True

    async def update_current_room_id(self: Self, character_id: uuid.UUID, room_id: str | None) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == character_id)
                .values(current_room_id=room_id)
            )
            await session.execute(stmt)
            return True

    async def commit(self) -> None:
        """Явный commit текущей транзакции"""
        await self.session.commit()
