import uuid

import sqlalchemy as sa

from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException
from ..enums import MiningStatus
from ..models import MiningAction
from ..schemas import MiningActionCreateSchema, MiningActionReadSchema, MiningActionUpdateSchema


class MiningActionRepositoryProtocol(
    BaseRepositoryImpl[
        MiningAction,
        MiningActionReadSchema,
        MiningActionCreateSchema,
        MiningActionUpdateSchema
    ]
):
    async def exists_processing_mining_action(self, character_id: uuid.UUID) -> bool:
        ...
        
    async def get_proccessing_mining_action(self, character_id: uuid.UUID) -> MiningActionReadSchema | None:
        """
        Получает текущие обрабатываемые действия майнинга для персонажа.
        Если таких действий нет, возвращает None.
        """

    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> MiningActionReadSchema:
        """
        Получает действие майнинга по его ID и ID персонажа.
        """

    async def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> MiningActionReadSchema:
        """
        Обновляет celery_task_id для действия майнинга.
        """

    async def cancel_mining(self,
                            action_id: uuid.UUID
                            ) -> MiningActionReadSchema:
        ...
   

class MiningActionRepository(MiningActionRepositoryProtocol):
    async def get_proccessing_mining_action(self, character_id: uuid.UUID) -> MiningActionReadSchema | None:
        async with self.session as session:
            stmt = (
                 sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.status == MiningStatus.IN_PROGRESS
                )
            )

            model = (await session.execute(stmt)).scalar_one_or_none()

            if model is None:
                return None
            
            return self.read_schema_type.model_validate(model, from_attributes=True)

    async def exists_processing_mining_action(self, character_id: uuid.UUID) -> bool:
        async with self.session as session:
            stmt = (
                sa.select(sa.exists().where(
                    self.model_type.character_id == character_id,
                    self.model_type.status == MiningStatus.IN_PROGRESS
                ))
            )
            
            result = await session.execute(stmt)
            return result.scalar()   
    async def get_for_character(self, action_id: uuid.UUID, character_id: uuid.UUID) -> MiningActionReadSchema:
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

            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def update_celery_task_id(
        self,
        action_id: uuid.UUID,
        celery_task_id: str
    ) -> MiningActionReadSchema:
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
        
    async def cancel_mining(self,
                            action_id: uuid.UUID
                            ) -> MiningActionReadSchema:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == action_id)
                .values(status=MiningStatus.CANCELLED)
            )

            await session.execute(stmt)

            return True