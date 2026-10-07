from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from shared.schemas.auth import UserTokenDataReadSchema
from ...characters.models import Character
from ..services.rest_service import RestServiceProtocol
from ..schemas import RestRentalReadSchema


class RentRoomUseCaseProtocol(UseCaseProtocol[RestRentalReadSchema]):
    async def __call__(self: Self, user: UserTokenDataReadSchema, days: int) -> RestRentalReadSchema: ...


class RentRoomUseCase(RentRoomUseCaseProtocol):
    def __init__(self, service: RestServiceProtocol, character_repository):
        self.service = service
        self.char_repo = character_repository

    async def __call__(self, user: UserTokenDataReadSchema, days: int) -> RestRentalReadSchema:
        if not user.character_id:
            from ....core.utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError()
        
        character = await self.char_repo.get(user.character_id)
        rental = await self.service.rent_room(character, days)
        return RestRentalReadSchema.model_validate(rental)