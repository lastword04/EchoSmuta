import logging
import traceback
import uuid

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import ValidationError
from ...enums import ItemType
from ...schemas import InventoryItemCreateSchema, InventoryItemReadSchema
from ...services.character.character_items import CharacterItemServiceProtocol

logger = logging.getLogger(__name__)


class UnpackKitUseCaseProtocol(UseCaseProtocol[list[InventoryItemReadSchema]]):
    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]: ...


class UnpackKitUseCase(UnpackKitUseCaseProtocol):
    def __init__(self, inventory_service: CharacterItemServiceProtocol):
        self.inventory_service = inventory_service

    async def __call__(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]:
        try:
            return await self._unpack(inventory_item_id, user)
        except Exception:
            logger.error("UNPACK TRACEBACK:\n%s", traceback.format_exc())
            raise

    async def _unpack(self, inventory_item_id: uuid.UUID, user: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]:
        # 1. Комплект должен принадлежать персонажу
        inventory_item = await self.inventory_service.get_by_id_and_character(
            inventory_item_id, user.character_id
        )

        if inventory_item is None:
            raise ValidationError(
                field="inventory_item_id",
                message="Предмет не найден в вашем инвентаре.",
            )

        # ═══ ЭСКРОУ: предмет в сделке «заморожен» — распаковывать нельзя ═══
        if getattr(inventory_item, "deal_id", None) is not None:
            raise ValidationError(
                field="deal_id",
                message="Предмет находится в сделке — сначала уберите его из сделки.",
            )

        # 2. Распаковать можно только KIT
        if inventory_item.item.item_type != ItemType.KIT:
            raise ValidationError(
                field="item_type",
                message="Этот предмет не является комплектом",
            )

        # 3. Состав комплекта
        kit_items = (inventory_item.item.parameters or {}).get("kit_items") or []
        if not kit_items:
            raise ValidationError(
                field="kit_items",
                message="У комплекта не указан состав",
            )

        # 4. Удаляем комплект из инвентаря (1 штука)
        await self.inventory_service.consume_item(inventory_item_id)

        # 5. Выдаём 6 частей (новые, с полной прочностью)
        created = []
        for item_slug in kit_items:
            created.append(
                await self.inventory_service.add_item(
                    user.character_id,
                    InventoryItemCreateSchema(item_slug=item_slug, amount=1),
                )
            )

        return created