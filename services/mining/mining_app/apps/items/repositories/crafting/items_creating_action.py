import uuid
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa

from .....core.repositories.base_repository import BaseRepositoryImpl
from .....core.utils.exceptions import ModelNotFoundException
from ...enums import ItemCreatingStatus
from ...models import ItemsCreatingAction
from ...schemas import (
    ItemsCreatingActionCreateSchema,
    ItemsCreatingActionReadSchema,
    ItemsCreatingActionUpdateSchema,
)


class ItemsCreatingActionRepositoryProtocol(
    BaseRepositoryImpl[
        ItemsCreatingAction,
        ItemsCreatingActionReadSchema,
        ItemsCreatingActionCreateSchema,
        ItemsCreatingActionUpdateSchema
    ]
):
    async def exists_processing_creating_action(self, character_id: uuid.UUID) -> bool:
        ...
        
    async def get_processing_creating_action(self, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema | None:
        """
        Получает текущие обрабатываемые действия крафта для персонажа.
        Если таких действий нет, возвращает None.
        """

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        """
        Получает действие крафта по его ID и ID персонажа.
        """

    async def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> ItemsCreatingActionReadSchema:
        """
        Обновляет celery_task_id для действия крафта.
        """

    async def cancel_creating(self, action_id: uuid.UUID) -> bool:
        """
        Отменяет действие крафта.
        """

    async def cancel_expired_for_character(
        self,
        character_id: uuid.UUID,
        older_than_minutes: int | None = None,
    ) -> int:
        """
        Отменяет IN_PROGRESS крафты персонажа (None — все; число — старше порога минут).
        При отмене истёкшего крафта также сбрасывает прогресс многоэтапного крафта
        (character_start_creating_items); активные крафты прогресс сохраняют.
        """


class ItemsCreatingActionRepository(ItemsCreatingActionRepositoryProtocol):
    async def get_processing_creating_action(self, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema | None:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.status == ItemCreatingStatus.IN_PROGRESS
                )
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                return None
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def exists_processing_creating_action(self, character_id: uuid.UUID) -> bool:
        async with self.session as session:
            stmt = (
                sa.select(sa.exists().where(
                    self.model_type.character_id == character_id,
                    self.model_type.status == ItemCreatingStatus.IN_PROGRESS
                ))
            )
            
            result = await session.execute(stmt)
            return result.scalar()
    
    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.id == action_id,
                    self.model_type.character_id == character_id
                )
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            if model is None:
                raise ModelNotFoundException(self.model_type, action_id)
            await session.refresh(model)
            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> ItemsCreatingActionReadSchema:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == action_id)
                .values(celery_task_id=celery_task_id)
                .returning(self.model_type)
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                raise ModelNotFoundException(self.model_type, action_id)

            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def cancel_creating(self, action_id: uuid.UUID) -> bool:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == action_id)
                .values(status=ItemCreatingStatus.CANCELLED)
            )

            await session.execute(stmt)

            return True

    async def cancel_expired_for_character(
        self,
        character_id: uuid.UUID,
        older_than_minutes: int | None = None,
    ) -> int:
        """
        Отменяет IN_PROGRESS крафты персонажа.

        older_than_minutes=None — отменяет ВСЕ IN_PROGRESS.
        Значение задано — только те, у кого finish_time < now - X минут.

        B2: если среди отменённых есть хотя бы один ИСТЁКШИЙ
        (finish_time < now - CANCEL_EXPIRED_GRACE_SECONDS), дополнительно
        удаляет строки character_start_creating_items персонажа (полный сброс
        прогресса многоэтапного крафта, чтобы /new работал).
        Активные (не истёкшие) крафты прогресс НЕ трогают — можно /continue.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Грейс против ложного «истёк» при обычной задержке celery-воркера
        CANCEL_EXPIRED_GRACE_SECONDS = 60

        if older_than_minutes is not None and older_than_minutes < 0:
            raise ValueError("older_than_minutes must be non-negative")

        from ...models import CharacterStartCreatingItem

        async with self.session as session, session.begin():
            now = datetime.now(UTC)
            expired_bound = now - timedelta(seconds=CANCEL_EXPIRED_GRACE_SECONDS)

            conditions = [
                self.model_type.character_id == character_id,
                self.model_type.status == ItemCreatingStatus.IN_PROGRESS,
            ]
            if older_than_minutes is not None:
                threshold = now - timedelta(minutes=older_than_minutes)
                conditions.append(self.model_type.finish_time < threshold)

            # 1. Читаем то, что собираемся отменить (нужно решить про сброс прогресса)
            # Используем SQL-подсчёт для проверки истечения, чтобы избежать проблем
            # с lazy-load/detached объектов после UPDATE.
            count_stmt = sa.select(sa.func.count()).select_from(self.model_type).where(*conditions)
            count_result = await session.execute(count_stmt)
            count = count_result.scalar()
            if count == 0:
                return 0

            # 2. Проверяем, есть ли истёкшие (finish_time < now - grace) среди IN_PROGRESS
            if older_than_minutes is not None:
                # Явный порог: все выбранные уже прошли finish_time < threshold
                has_expired = True
            else:
                # None: cancel ALL, но сбрасываем прогресс только для истёкших
                expired_count_stmt = sa.select(sa.func.count()).select_from(self.model_type).where(
                    self.model_type.character_id == character_id,
                    self.model_type.status == ItemCreatingStatus.IN_PROGRESS,
                    self.model_type.finish_time < expired_bound,
                )
                expired_count = (await session.execute(expired_count_stmt)).scalar()
                has_expired = expired_count > 0

            # 3. Отменяем
            cancel_stmt = (
                sa.update(self.model_type)
                .where(*conditions)
                .values(status=ItemCreatingStatus.CANCELLED)
            )
            result = await session.execute(cancel_stmt)

            # 4. Полный сброс прогресса ТОЛЬКО если есть истёкший крафт
            if has_expired:
                delete_stmt = sa.delete(CharacterStartCreatingItem).where(
                    CharacterStartCreatingItem.character_id == character_id
                )
                await session.execute(delete_stmt)
                logger.info(
                    "[cancel_expired] Expired crafting detected for character %s — "
                    "character_start_creating_items reset",
                    character_id,
                )

            logger.info(
                "[cancel_expired] Cancelled %s craftings for character %s (expired=%s)",
                result.rowcount, character_id, has_expired,
            )
            return result.rowcount
    
