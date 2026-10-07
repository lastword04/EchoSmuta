import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ....core.utils.exceptions import ModelNotFoundException
from ..enums import MiningStatus
from ..models import MiningAction
from ..schemas import MiningActionReadSchema, MiningActionUpdateSchema


class MiningActionSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def exists_processing_mining_action(self, character_id: uuid.UUID) -> bool:
        stmt = (
            sa.select(sa.exists().where(
                MiningAction.character_id == character_id,
                MiningAction.status == MiningStatus.IN_PROGRESS
            ))
        )
        result = self.session.execute(stmt)
        return result.scalar()

    def get_proccessing_mining_action(self, character_id: uuid.UUID) -> MiningActionReadSchema | None:
        stmt = (
            sa.select(MiningAction)
            .where(
                MiningAction.character_id == character_id,
                MiningAction.status == MiningStatus.IN_PROGRESS
            )
        )
        model = self.session.execute(stmt).scalar_one_or_none()

        if model is None:
            return None

        return MiningActionReadSchema.model_validate(model, from_attributes=True)

    def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> MiningActionReadSchema:
        stmt = (
            sa.select(MiningAction)
            .where(
                MiningAction.id == action_id,
                MiningAction.character_id == character_id
            )
        )
        model = self.session.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ModelNotFoundException(MiningAction, action_id)

        return MiningActionReadSchema.model_validate(model, from_attributes=True)

    def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> MiningActionReadSchema:
        stmt = (
            sa.update(MiningAction)
            .where(MiningAction.id == action_id)
            .values(celery_task_id=celery_task_id)
            .returning(MiningAction)
        )
        model = self.session.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ModelNotFoundException(MiningAction, action_id)

        return MiningActionReadSchema.model_validate(model, from_attributes=True)

    def cancel_mining(self, action_id: uuid.UUID) -> bool:
        stmt = (
            sa.update(MiningAction)
            .where(MiningAction.id == action_id)
            .values(status=MiningStatus.CANCELLED)
        )
        self.session.execute(stmt)
        return True

    def update(self, action_update: "MiningActionUpdateSchema") -> MiningActionReadSchema:
        """Обновить mining action по id из schema."""
        update_data = action_update.model_dump(exclude={"id"})
        stmt = (
            sa.update(MiningAction)
            .where(MiningAction.id == action_update.id)
            .values(**update_data)
            .returning(MiningAction)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            from ....core.utils.exceptions import ModelNotFoundException
            raise ModelNotFoundException(MiningAction, action_update.id)
        return MiningActionReadSchema.model_validate(model, from_attributes=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()