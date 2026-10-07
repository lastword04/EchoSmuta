from shared.schemas.characters import CharacterReadSchema
from shared.schemas.auth import UserTokenDataReadSchema
from ...repositories.character.characters import CharacterRepositoryProtocol
from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...services.locations.character_location import CharacterLocationServiceProtocol
from ....stats.services.effective_stats import EffectiveStatsService
from ....rest.services.house_guest_service import HouseGuestServiceProtocol
from ....rest.services.rest_service import RestServiceProtocol

class ChangeCharacterLocationUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(
        self,
        location_slug: str,
        user: UserTokenDataReadSchema
    ) -> CharacterReadSchema:
        ...

class ChangeCharacterLocationUseCase(ChangeCharacterLocationUseCaseProtocol):
    def __init__(
        self,
        service: CharacterLocationServiceProtocol,
        effective_stats: EffectiveStatsService,
        house_guest_service: HouseGuestServiceProtocol,
        rest_service: RestServiceProtocol,
        character_repository: CharacterRepositoryProtocol,
    ):
        self.service = service
        self.effective_stats = effective_stats
        self.house_guest_service = house_guest_service
        self.rest_service = rest_service
        self.character_repository = character_repository

    async def __call__(
        self,
        location_slug: str,
        user: UserTokenDataReadSchema
    ) -> CharacterReadSchema:
        if not user.character_id:
            raise PermissionDeniedError()
        
        character = await self.service.update_character_location(
            character_id=user.character_id,
            location_slug=location_slug
        )

        await self.house_guest_service.leave_on_location_change(character, location_slug)
        await self.rest_service.sync_on_location_change(character, location_slug)

        # Перечитываем персонажа: синхронизации выше могли изменить
        # rest_state / current_house_id, а фронт должен получить актуальные значения.
        character = await self.character_repository.get(user.character_id)
        
        effective = await self.effective_stats.calculate(character)
        for key, value in effective.items():
            setattr(character, key, value)
        
        return character