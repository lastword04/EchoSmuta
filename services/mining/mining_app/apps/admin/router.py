import uuid

from fastapi import APIRouter, Depends, Query

from shared.schemas.auth import UserTokenDataReadSchema

from ..items.deals.schemas import CompletingDealListSchema
from ..items.deals.use_cases import ListCompletingDealsUseCase
from ..items.deps.deals import get_list_completing_deals_use_case
from ..items.enums import ItemType
from .depends import get_admin_mutation_service, get_admin_read_service, require_admin
from .schemas import (
    AdminCharacterDetailsSchema,
    AdminCharacterListSchema,
    AdminCharacterResourceSchema,
    AdminGiveItemSchema,
    AdminInventoryGroupsSchema,
    AdminItemCatalogListSchema,
    AdminItemTypeSchema,
    AdminLogListSchema,
    AdminMoneyAddSchema,
    AdminMoneySetSchema,
    AdminMutationResultSchema,
    AdminResourceCategorySchema,
    AdminResourceListSchema,
    AdminResourceMutationSchema,
    AdminTakeItemSchema,
)
from .services.admin_mutations import AdminMutationServiceProtocol
from .services.admin_read import AdminReadService

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/characters", response_model=AdminCharacterListSchema)
async def list_characters(search: str | None = Query(None, max_length=100), limit: int = Query(50, gt=0, le=100), offset: int = Query(0, ge=0), service: AdminReadService = Depends(get_admin_read_service)) -> AdminCharacterListSchema:
    return await service.list_characters(search, min(limit, 50), offset)


@router.get("/characters/{character_id}", response_model=AdminCharacterDetailsSchema)
async def get_character(character_id: uuid.UUID, service: AdminReadService = Depends(get_admin_read_service)) -> AdminCharacterDetailsSchema:
    return await service.get_character(character_id)


@router.get("/characters/{character_id}/inventory", response_model=AdminInventoryGroupsSchema)
async def get_character_inventory(character_id: uuid.UUID, service: AdminReadService = Depends(get_admin_read_service)) -> AdminInventoryGroupsSchema:
    return await service.get_inventory(character_id)


@router.get("/characters/{character_id}/resources", response_model=list[AdminCharacterResourceSchema])
async def get_character_resources(character_id: uuid.UUID, service: AdminReadService = Depends(get_admin_read_service)) -> list[AdminCharacterResourceSchema]:
    return await service.get_character_resources(character_id)


@router.get("/items", response_model=AdminItemCatalogListSchema)
async def list_items(item_type: ItemType | None = None, location_slug: str | None = Query(None, max_length=128), search: str | None = Query(None, max_length=128), limit: int = Query(50, gt=0, le=100), offset: int = Query(0, ge=0), service: AdminReadService = Depends(get_admin_read_service)) -> AdminItemCatalogListSchema:
    return await service.list_items(item_type, location_slug, search, limit, offset)


@router.get("/resources", response_model=AdminResourceListSchema)
async def list_resources(category: str | None = Query(None, max_length=32), search: str | None = Query(None, max_length=128), limit: int = Query(50, gt=0, le=100), offset: int = Query(0, ge=0), service: AdminReadService = Depends(get_admin_read_service)) -> AdminResourceListSchema:
    return await service.list_resources(category, search, limit, offset)


@router.get("/item-types", response_model=list[AdminItemTypeSchema])
async def get_item_types(service: AdminReadService = Depends(get_admin_read_service)) -> list[AdminItemTypeSchema]:
    return await service.item_types()


@router.get("/resource-categories", response_model=list[AdminResourceCategorySchema])
async def get_resource_categories(service: AdminReadService = Depends(get_admin_read_service)) -> list[AdminResourceCategorySchema]:
    return await service.resource_categories()


@router.post("/characters/{character_id}/items/give", response_model=AdminMutationResultSchema)
async def give_item(character_id: uuid.UUID, data: AdminGiveItemSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.give_item(admin, character_id, data)


@router.post("/characters/{character_id}/items/take", response_model=AdminMutationResultSchema)
async def take_item(character_id: uuid.UUID, data: AdminTakeItemSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.take_item(admin, character_id, data)


@router.post("/characters/{character_id}/resources/give", response_model=AdminMutationResultSchema)
async def give_resource(character_id: uuid.UUID, data: AdminResourceMutationSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.give_resource(admin, character_id, data)


@router.post("/characters/{character_id}/resources/take", response_model=AdminMutationResultSchema)
async def take_resource(character_id: uuid.UUID, data: AdminResourceMutationSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.take_resource(admin, character_id, data)


@router.post("/characters/{character_id}/money/add", response_model=AdminMutationResultSchema)
async def add_money(character_id: uuid.UUID, data: AdminMoneyAddSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.add_money(admin, character_id, data)


@router.post("/characters/{character_id}/money/set", response_model=AdminMutationResultSchema)
async def set_money(character_id: uuid.UUID, data: AdminMoneySetSchema, admin: UserTokenDataReadSchema = Depends(require_admin), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminMutationResultSchema:
    return await service.set_money(admin, character_id, data)


@router.get("/logs", response_model=AdminLogListSchema)
async def list_logs(character_id: uuid.UUID | None = None, limit: int = Query(50, gt=0, le=100), offset: int = Query(0, ge=0), service: AdminMutationServiceProtocol = Depends(get_admin_mutation_service)) -> AdminLogListSchema:
    return await service.list_logs(character_id, limit, offset)


@router.get("/deals/completing", response_model=CompletingDealListSchema)
async def list_completing_deals(
    limit: int = Query(50, gt=0, le=200),
    use_case: ListCompletingDealsUseCase = Depends(get_list_completing_deals_use_case)
) -> CompletingDealListSchema:
    return await use_case(limit)