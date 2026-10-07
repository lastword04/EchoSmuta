from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from .....settings import settings
from ...schemas import GlobalCharacterSettingsCreateSchema, GlobalCharacterSettingsReadSchema
from ...services.settings.global_settings import GlobalCharacterSettingsServiceProtocol 


class InitializeGlobalCharacterSettingsUseCaseProtocol(UseCaseProtocol[GlobalCharacterSettingsReadSchema]):
    async def __call__(self: Self) -> GlobalCharacterSettingsReadSchema:
        ...


class InitializeGlobalCharacterSettingsUseCase(InitializeGlobalCharacterSettingsUseCaseProtocol):
    def __init__(self: Self, service: GlobalCharacterSettingsServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> GlobalCharacterSettingsReadSchema:
         
        global_settings = await self.service.get_all()
        if len(global_settings) > 0:
            return global_settings

        default_global_settings = self._get_default_global_settings()
        return await self.service.create(default_global_settings)

    def _get_default_global_settings(self: Self) -> GlobalCharacterSettingsCreateSchema:
        return GlobalCharacterSettingsCreateSchema(
            default_health=settings.global_character_settings.default_health,
            default_max_health=settings.global_character_settings.default_max_health,
            default_mana=settings.global_character_settings.default_mana,
            default_max_mana=settings.global_character_settings.default_max_mana,
            default_tiredness=settings.global_character_settings.default_tiredness,
            default_max_tiredness=settings.global_character_settings.default_max_tiredness,
            default_experience=settings.global_character_settings.default_experience,
            default_level=settings.global_character_settings.default_level,
            default_endurance=settings.global_character_settings.default_endurance,
            default_intelligence=settings.global_character_settings.default_intelligence,
            default_weight=settings.global_character_settings.default_weight,
            default_max_weight=settings.global_character_settings.default_max_weight,
            default_gold=settings.global_character_settings.default_gold,
            default_ducats=settings.global_character_settings.default_ducats,
            health_multiplier=settings.global_character_settings.health_multiplier,
            mana_multiplier=settings.global_character_settings.mana_multiplier,
            max_characters_on_user=settings.global_character_settings.max_characters_on_user
        )