import uuid
import sqlalchemy as sa
from typing import Optional
from typing_extensions import Self
from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import MailRecieveSettings
from ..schemas import MailRecieveSettingsCreateSchema, MailRecieveSettingsUpdateSchema, MailRecieveSettingsReadSchema

class MailReceiveSettingsRepositoryProtocol(
    BaseRepositoryImpl[
        MailRecieveSettings,
        MailRecieveSettingsReadSchema,
        MailRecieveSettingsCreateSchema,
        MailRecieveSettingsUpdateSchema
    ]
):
    async def get_by_character_or_none(self: Self, character_id: uuid.UUID) -> Optional[MailRecieveSettingsReadSchema]:
        ...

    async def delete_by_character_id(self: Self, character_id: uuid.UUID) -> bool:
        ...


class MailReceiveSettingsRepository(MailReceiveSettingsRepositoryProtocol):
    async def get_by_character_or_none(self: Self, character_id: uuid.UUID) -> Optional[MailRecieveSettingsReadSchema]:
        async with self.session as s:
            statement = (
                sa.select(self.model_type)
                .where(self.model_type.character_id == character_id)
            )

            model = (await s.execute(statement)).scalar_one_or_none()

            if model is None:
                return None
            
            return self.read_schema_type.model_validate(model, from_attributes=True)
        
    async def delete_by_character_id(self: Self, character_id: uuid.UUID) -> bool:
        async with self.session as s, s.begin():
            statement = (
                sa.delete(self.model_type)
                .where(self.model_type.character_id == character_id)
            )

            await s.execute(statement)

            return True

