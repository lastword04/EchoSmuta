from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import InventoryItemReadSchema
from ...services.character.equipment import EquipmentServiceProtocol


class GetMyEquipmentUseCaseProtocol(UseCaseProtocol[list[InventoryItemReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]: ...


class GetMyEquipmentUseCase(GetMyEquipmentUseCaseProtocol):
    def __init__(self: Self, equipment_service: EquipmentServiceProtocol):
        self.equipment_service = equipment_service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        return await self.equipment_service.get_equipped_items(token.character_id)