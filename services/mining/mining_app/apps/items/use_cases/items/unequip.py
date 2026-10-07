import uuid

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from .....core.use_cases import UseCaseProtocol
from ...services.character.equipment import EquipmentServiceProtocol


class UnequipItemUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> StatusOkSchema: ...


class UnequipItemUseCase(UnequipItemUseCaseProtocol):
    def __init__(self, service: EquipmentServiceProtocol): self.service = service
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> StatusOkSchema:
        await self.service.unequip(user.character_id, inventory_item_id)
        return StatusOkSchema()
