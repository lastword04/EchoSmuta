import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .....core.utils.exceptions import ModelNotFoundException
from ...enums import ItemCreatingStatus
from ...models import ItemsCreatingAction
from ...schemas import (
    ItemsCreatingActionCreateSchema,
    ItemsCreatingActionReadSchema,
    ItemsCreatingActionUpdateSchema,
)


class ItemsCreatingActionSyncRepository:
    """Синхронная версия репозитория для ItemsCreatingAction (для Celery)"""

    def __init__(self, session: Session):
        self.session = session
        self.model_type = ItemsCreatingAction
        self.read_schema_type = ItemsCreatingActionReadSchema

    def get_processing_creating_action(self, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema | None:
        stmt = (
            sa.select(self.model_type)
            .where(
                self.model_type.character_id == character_id,
                self.model_type.status == ItemCreatingStatus.IN_PROGRESS
            )
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def exists_processing_creating_action(self, character_id: uuid.UUID) -> bool:
        stmt = (
            sa.select(sa.exists().where(
                self.model_type.character_id == character_id,
                self.model_type.status == ItemCreatingStatus.IN_PROGRESS
            ))
        )
        result = self.session.execute(stmt)
        return result.scalar()

    def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> ItemsCreatingActionReadSchema:
        stmt = (
            sa.select(self.model_type)
            .where(
                self.model_type.id == action_id,
                self.model_type.character_id == character_id
            )
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ModelNotFoundException(self.model_type, action_id)
        # Принудительно обновляем модель из БД
        self.session.refresh(model)
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> ItemsCreatingActionReadSchema:
        stmt = (
            sa.update(self.model_type)
            .where(self.model_type.id == action_id)
            .values(celery_task_id=celery_task_id)
            .returning(self.model_type)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ModelNotFoundException(self.model_type, action_id)
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def cancel_creating(self, action_id: uuid.UUID) -> bool:
        stmt = (
            sa.update(self.model_type)
            .where(self.model_type.id == action_id)
            .values(status=ItemCreatingStatus.CANCELLED)
        )
        self.session.execute(stmt)
        return True

    def create(self, data: ItemsCreatingActionCreateSchema) -> ItemsCreatingActionReadSchema:
        """Создать новое действие"""
        model = self.model_type(
            character_id=data.character_id,
            location_slug=data.location_slug,
            start_time=data.start_time,
            finish_time=data.finish_time,
            status=data.status,
            message=data.message,
            quantity=data.quantity,
            craft_stage=data.craft_stage,
        )
        self.session.add(model)
        self.session.flush()
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def update(self, data: ItemsCreatingActionUpdateSchema) -> ItemsCreatingActionReadSchema:
        """Обновить действие"""
        model = self.session.get(self.model_type, data.id)
        if model is None:
            raise ModelNotFoundException(self.model_type, data.id)
        for key, value in data.model_dump(exclude={'id'}).items():
            setattr(model, key, value)
        self.session.flush()
        return self.read_schema_type.model_validate(model, from_attributes=True)

    def commit(self):
        """Зафиксировать транзакцию"""
        self.session.commit()

    def rollback(self):
        """Откатить транзакцию"""
        self.session.rollback()

    def close(self):
        """Закрыть сессию"""
        self.session.close()