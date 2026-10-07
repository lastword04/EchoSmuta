import uuid

from fastapi import APIRouter, Depends, Path

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from ....core.depends import get_user_token_payload
from ....core.utils.exceptions import PermissionDeniedError
from ..deps.items import (
    get_equip_item_use_case,
    get_equipment_service,
    get_get_item_by_slug_use_case,
    get_get_item_details_use_case,
    get_get_my_equipment_use_case,
    get_repair_item_use_case,
    get_unequip_item_use_case,
    get_unpack_kit_use_case,
    get_use_consumable_use_case,
)
from ..schemas import (
    CharacterEquipmentReadSchema,
    InventoryItemReadSchema,
    ItemDetailsSchema,
    ItemReadSchema,
)
from ..services.character.equipment import EquipmentServiceProtocol
from ..use_cases.items.equip import EquipItemUseCaseProtocol
from ..use_cases.items.get_item_by_slug import GetItemBySlugUseCaseProtocol
from ..use_cases.items.get_item_details import GetItemDetailsUseCaseProtocol
from ..use_cases.items.get_my_equipment import GetMyEquipmentUseCaseProtocol
from ..use_cases.items.repair import RepairItemUseCaseProtocol
from ..use_cases.items.unequip import UnequipItemUseCaseProtocol
from ..use_cases.items.unpack_kit import UnpackKitUseCaseProtocol
from ..use_cases.items.use_consumable import UseConsumableUseCaseProtocol

router = APIRouter()


@router.post('/equip/{inventory_item_id}', response_model=CharacterEquipmentReadSchema)
async def equip_item(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: EquipItemUseCaseProtocol = Depends(get_equip_item_use_case),
) -> CharacterEquipmentReadSchema:
    return await use_case(inventory_item_id, user)


@router.post('/unequip/{inventory_item_id}', response_model=StatusOkSchema)
async def unequip_item(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UnequipItemUseCaseProtocol = Depends(get_unequip_item_use_case),
) -> StatusOkSchema:
    return await use_case(inventory_item_id, user)

@router.post('/unpack/{inventory_item_id}', response_model=list[InventoryItemReadSchema])
async def unpack_kit(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UnpackKitUseCaseProtocol = Depends(get_unpack_kit_use_case),
) -> list[InventoryItemReadSchema]:
    """Распаковать комплект брони на 6 отдельных частей"""
    return await use_case(inventory_item_id, user)


@router.get('/equipment/me', response_model=list[InventoryItemReadSchema])
async def get_my_equipment(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyEquipmentUseCaseProtocol = Depends(get_get_my_equipment_use_case),
) -> list[InventoryItemReadSchema]:
    return await use_case(user)


@router.get('/equipment/bonuses/me', response_model=dict)
async def get_my_equipment_bonuses(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    equipment_service: EquipmentServiceProtocol = Depends(get_equipment_service)
) -> dict:
    """
    Возвращает актуальные суммарные бонусы экипировки текущего персонажа.
    
    Используется фронтом для получения свежих бонусов сразу после equip/unequip.
    Требует user token.
    
    Returns:
        dict: {"bonuses": {"strength_bonus": 10, "defense": 20, ...}}
    """
    if not user.character_id:
        raise PermissionDeniedError()
    
    bonuses = await equipment_service.get_equipment_bonuses(user.character_id)
    return {"bonuses": bonuses}

@router.post("/{inventory_item_id}/use", response_model=StatusOkSchema)
async def use_item(
    inventory_item_id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload), 
    use_case: UseConsumableUseCaseProtocol = Depends(get_use_consumable_use_case)
) -> StatusOkSchema:
    return await use_case(inventory_item_id, user) 


@router.post('/repair/{inventory_item_id}', response_model=InventoryItemReadSchema)
async def repair_item(
    inventory_item_id: uuid.UUID = Path(..., description="ID of the inventory item"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: RepairItemUseCaseProtocol = Depends(get_repair_item_use_case),
) -> InventoryItemReadSchema:
    return await use_case(inventory_item_id, user)

@router.get('/item/{item_slug}', response_model=ItemReadSchema)
async def get_item_by_slug(
    item_slug: str = Path(..., description="Slug of the item"),
    use_case: GetItemBySlugUseCaseProtocol = Depends(get_get_item_by_slug_use_case)
) -> ItemReadSchema:
    return await use_case(item_slug)

@router.get('/{item_id}/details', response_model=ItemDetailsSchema)
async def get_item_details(
    item_id: uuid.UUID = Path(..., description="ID of the item"),
    use_case: GetItemDetailsUseCaseProtocol = Depends(get_get_item_details_use_case)
) -> ItemDetailsSchema:
    return await use_case(item_id)
