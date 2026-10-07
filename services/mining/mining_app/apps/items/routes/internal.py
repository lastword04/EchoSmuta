import uuid

from fastapi import APIRouter, Depends

from ....core.depends import get_service_token_payload
from ..deals.schemas import TradeLicenseStatusSchema
from ..deals.use_cases import TradeLicenseUseCase
from ..deps.deals import get_trade_license_use_case
from ..deps.items import get_character_item_repository, get_equipment_service
from ..schemas import InternalFurnitureItemSchema, InternalFurnitureBulkRequestSchema, InternalFurnitureWearRequestSchema, InternalFurnitureWearResponseSchema
from ..services.character.equipment import EquipmentServiceProtocol

router = APIRouter()


@router.get('/internal/trade-licenses/{character_id}/active', response_model=TradeLicenseStatusSchema)
async def get_active_trade_license(character_id: uuid.UUID, token: dict = Depends(get_service_token_payload), use_case: TradeLicenseUseCase = Depends(get_trade_license_use_case)) -> TradeLicenseStatusSchema:
    return await use_case.status(character_id)


# Equipment Bonuses Internal Endpoint

@router.get(
    '/internal/equipment/{character_id}/bonuses',
    response_model=dict,
    summary="Получить бонусы экипировки (internal)",
    description="Внутренний endpoint для получения суммарных бонусов экипировки. Требует service token."
)
async def get_equipment_bonuses(
    character_id: uuid.UUID,
    token: dict = Depends(get_service_token_payload),
    equipment_service: EquipmentServiceProtocol = Depends(get_equipment_service)
) -> dict:
    """
    Возвращает суммарные бонусы экипировки персонажа.
    
    Используется Characters сервисом для recovery при входе в игру.
    Требует service token.
    """
    bonuses = await equipment_service.get_equipment_bonuses(character_id)
    return {"bonuses": bonuses}


@router.get(
    '/internal/inventory/{character_id}/furniture',
    response_model=list[InternalFurnitureItemSchema],
)
async def get_character_furniture(
    character_id: uuid.UUID,
    token: dict = Depends(get_service_token_payload),
    repository=Depends(get_character_item_repository),
):
    return await repository.get_character_furniture(character_id)


@router.post(
    '/internal/inventory/furniture/bulk',
    response_model=list[InternalFurnitureItemSchema],
    summary="Чтение мебели пачкой (internal)",
)
async def get_furniture_bulk(
    request: InternalFurnitureBulkRequestSchema,
    token: dict = Depends(get_service_token_payload),
    repository=Depends(get_character_item_repository),
):
    return await repository.get_furniture_bulk(request.inventory_item_ids)


@router.post(
    '/internal/inventory/furniture/wear',
    response_model=InternalFurnitureWearResponseSchema,
    summary="Инкремент износа мебели пачкой (internal)",
)
async def add_furniture_wear(
    request: InternalFurnitureWearRequestSchema,
    token: dict = Depends(get_service_token_payload),
    repository=Depends(get_character_item_repository),
):
    broken_ids = await repository.add_wear_bulk(
        [(e.inventory_item_id, e.wear_add) for e in request.entries]
    )
    return InternalFurnitureWearResponseSchema(broken_ids=broken_ids)
