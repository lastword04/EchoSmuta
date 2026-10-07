import uuid

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...schemas import InventoryItemReadSchema
from ...services.character.equipment import EquipmentServiceProtocol


class RepairItemUseCaseProtocol(UseCaseProtocol[InventoryItemReadSchema]):
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> InventoryItemReadSchema: ...


class RepairItemUseCase(RepairItemUseCaseProtocol):
    def __init__(self, service: EquipmentServiceProtocol): self.service = service
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> InventoryItemReadSchema:
        return await self.service.repair(user.character_id, inventory_item_id)
