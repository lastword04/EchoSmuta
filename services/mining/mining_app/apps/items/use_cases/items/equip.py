import uuid

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import ValidationError
from ...adapters.characters import CharacterServiceClientProtocol
from ...enums import ItemType
from ...requirements import check_item_requirements
from ...schemas import CharacterEquipmentReadSchema
from ...services.character.character_items import CharacterItemServiceProtocol
from ...services.character.equipment import EquipmentServiceProtocol


class EquipItemUseCaseProtocol(UseCaseProtocol[CharacterEquipmentReadSchema]):
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> CharacterEquipmentReadSchema: ...


class EquipItemUseCase(EquipItemUseCaseProtocol):
    def __init__(
        self,
        service: EquipmentServiceProtocol,
        inventory_service: CharacterItemServiceProtocol,
        characters_client: CharacterServiceClientProtocol,
    ):
        self.service = service
        self.inventory_service = inventory_service
        self.characters_client = characters_client

    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> CharacterEquipmentReadSchema:
        inventory_item = await self.inventory_service.get_by_id_and_character(
            inventory_item_id, user.character_id
        )

        if inventory_item is None:
            raise ValidationError(
                field="inventory_item_id",
                message="Предмет не найден в вашем инвентаре.",
            )

        # ═══ ЭКСКРОУ: предмет в сделке — надевать нельзя ═══
        # Иначе после подтверждения сделки предмет уйдёт партнёру,
        # а запись в character_equipment останется у отправителя.
        if inventory_item.deal_id is not None:
            raise ValidationError(
                field="deal_id",
                message="Предмет находится в сделке — сначала уберите его из сделки.",
            )

        # ═══ КОМПЛЕКТ НЕЛЬЗЯ НАДЕТЬ — только распаковать ═══
        if inventory_item.item.item_type == ItemType.KIT:
            raise ValidationError(
                field="item_type",
                message="Это комплект брони. Его нельзя экипировать — сначала распакуйте его.",
            )

        # ═══ ПРОВЕРКА ТРЕБОВАНИЙ (уровень, раса, статы) ═══
        character = await self.characters_client.get_character_for_requirements(user.character_id)
        check_item_requirements(inventory_item.item, character)

        return await self.service.equip(user.character_id, inventory_item_id)