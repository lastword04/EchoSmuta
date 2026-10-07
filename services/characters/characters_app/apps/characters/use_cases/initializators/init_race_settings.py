from typing_extensions import Self
from shared.enums import Race
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import RaceSettingsCreateSchema, RaceSettingsReadSchema
from ...services.settings.race_settings import RaceSettingsServiceProtocol 


class InitializeRaceSettingsUseCaseProtocol(UseCaseProtocol[RaceSettingsReadSchema]):
    async def __call__(self: Self) -> RaceSettingsReadSchema:
        ...


class InitializeRaceSettingsUseCase(InitializeRaceSettingsUseCaseProtocol):
    def __init__(self: Self, service: RaceSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> RaceSettingsReadSchema:
         
        race_settings = await self.service.get_all()
        if len(race_settings) == len(Race):
            return race_settings

        default_race_settings = self._get_default_race_settings()
        return await self.service.bulk_create(default_race_settings)

    def _get_default_race_settings(self: Self) -> list[RaceSettingsCreateSchema]:
        return [
            RaceSettingsCreateSchema(
                race=Race.HUMAN,
                base_power=settings.race_settings.human.base_power,
                base_agility=settings.race_settings.human.base_agility,
                base_lucky=settings.race_settings.human.base_lucky
            ),
            RaceSettingsCreateSchema(
                race=Race.ELF,
                base_power=settings.race_settings.elf.base_power,
                base_agility=settings.race_settings.elf.base_agility,
                base_lucky=settings.race_settings.elf.base_lucky
            ),
            RaceSettingsCreateSchema(
                race=Race.ORC,
                base_power=settings.race_settings.orc.base_power,
                base_agility=settings.race_settings.orc.base_agility,
                base_lucky=settings.race_settings.orc.base_lucky
            )
        ]