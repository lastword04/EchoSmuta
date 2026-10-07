import sqlalchemy as sa
from shared.enums import Race
from .....core.repositories.base_repository import BaseRepositoryImpl
from ...models import RaceSettings
from ...schemas import RaceSettingsReadSchema, RaceSettingsCreateSchema, RaceSettingsUpdateDBSchema

class RaceSettingsRepositoryProtocol(BaseRepositoryImpl[
    RaceSettings,
    RaceSettingsReadSchema,
    RaceSettingsCreateSchema,
    RaceSettingsUpdateDBSchema
]):
    async def get_by_race(self, race: Race) -> RaceSettingsReadSchema | None:
        ...


class RaceSettingsRepository(RaceSettingsRepositoryProtocol):
    async def get_by_race(self, race: Race) -> RaceSettingsReadSchema | None:
        async with self.session as session:
            stmt = (
                sa.select(self.model_type)
                .where(self.model_type.race == race)
            )
            model = (await session.execute(stmt)).scalar_one_or_none()  

            if not model:
                return None

            return self.read_schema_type.model_validate(model, from_attributes=True)