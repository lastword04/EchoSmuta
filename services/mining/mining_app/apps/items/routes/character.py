import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, Path, Query, Request
from PIL import Image

from shared.schemas.auth import UserTokenDataReadSchema

from ....core.depends import get_user_token_payload
from ....core.utils.exceptions import (
    ModelFieldNotFoundException,
    PermissionDeniedError,
    ValidationError,
)
from ..deps.adapters import get_file_service_client
from ..deps.character import (
    get_create_ct_shop_use_case,
    get_get_character_items_use_case,
    get_get_ct_shop_by_id_use_case,
    get_get_ct_shop_by_number_use_case,
    get_get_ct_shop_for_character_use_case,
    get_get_items_from_location_use_case,
    get_get_shops_with_sale_items_paginated_use_case,
    get_level_up_ct_shop_use_case,
    get_update_info_ct_shop_use_case,
    get_update_license_duration_ct_shop_use_case,
    get_update_photo_ct_shop_use_case,
    get_upgrade_ct_shop_use_case,
)
from ..schemas import (
    CityTradingShopReadSchema,
    CityTradingShopResponseSchema,
    CityTradingShopUpdateInfoSchema,
    CityTradingShopUpdatePhotoSchema,
    InventoryItemReadSchema,
    LocationItemsGroupedSchema,
    PaginatedShopsWithSaleItemsSchema,
)
from ..use_cases.character.create import CreateCTShopUseCaseProtocol
from ..use_cases.character.get import GetCTShopByIdUseCaseProtocol
from ..use_cases.character.get_by_number import GetCTShopByNumberUseCaseProtocol
from ..use_cases.character.get_character_items import GetCharacterItemsUseCaseProtocol
from ..use_cases.character.get_city_shop_for_character import (
    GetCTShopForCharacterUseCaseProtocol,
)
from ..use_cases.character.get_items_from_location import (
    GetItemsFromLocationUseCaseProtocol,
)
from ..use_cases.character.get_shops_with_sale_items_paginated import (
    GetShopsWithSaleItemsPaginatedUseCaseProtocol,
)
from ..use_cases.character.level_up_shop import LevelUpCTShopUseCaseProtocol
from ..use_cases.character.update_info import UpdateInfoCTShopUseCaseProtocol
from ..use_cases.character.update_license_duration import (
    UpdateLicenseCTShopUseCaseProtocol,
)
from ..use_cases.character.update_photo import UpdatePhotoCTShopUseCaseProtocol
from ..use_cases.character.upgrade_shop import UpgradeCTShopUseCaseProtocol

router = APIRouter()


@router.get('/city-shop', response_model=CityTradingShopResponseSchema | None)
async def get_city_shop_for_character(
    location_slug: str = Query(None, min_length=1, max_length=128),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCTShopForCharacterUseCaseProtocol = Depends(get_get_ct_shop_for_character_use_case),
) -> CityTradingShopResponseSchema | None:
    try:
        return await use_case(user, location_slug)
    except ModelFieldNotFoundException as e:
        # «Нет лавки» — валидное состояние, а не ошибка: отвечаем 200 + null.
        # Точечная проверка модели: чужие "не найдено" (персонаж и пр.) остаются 404
        if e.model.__name__ != 'CityTradingShop':
            raise
        return None

@router.get('/city-shop/number/{number}', response_model=CityTradingShopResponseSchema)
async def get_city_shop_by_number(
    number: int = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCTShopByNumberUseCaseProtocol = Depends(get_get_ct_shop_by_number_use_case)
) -> CityTradingShopResponseSchema:
    return await use_case(number, user)

@router.get('/city-shop/paginate', response_model=PaginatedShopsWithSaleItemsSchema)
async def get_shops_with_sale_items_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(5, ge=1, le=500, description="Items per page"),
    item_name: str = Query(None, min_length=1, max_length=128, description="Filter by item name"),
    number: int = Query(None, ge=1, description="Filter by shop number"),
    minimal_level: int = Query(None, ge=1, description="Filter by item minimal level"),
    item_kind: str = Query(None, max_length=32, description="Filter by item kind"),
    location_slug: str | None = Query(None, min_length=1, max_length=128, description="Optional location slug from frontend"),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetShopsWithSaleItemsPaginatedUseCaseProtocol = Depends(get_get_shops_with_sale_items_paginated_use_case)
) -> PaginatedShopsWithSaleItemsSchema:
    return await use_case(
        page, page_size, user,
        item_name=item_name,
        number=number,
        minimal_level=minimal_level,
        item_kind=item_kind,
        location_slug=location_slug,
    )

@router.get('/city-shop/{id}', response_model=CityTradingShopResponseSchema)
async def get_city_shop_by_id(
    id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCTShopByIdUseCaseProtocol = Depends(get_get_ct_shop_by_id_use_case)
) -> CityTradingShopResponseSchema:
    return await use_case(id, user)

@router.post('/city-shop/', response_model=CityTradingShopResponseSchema, status_code=201)
async def create_city_shop(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateCTShopUseCaseProtocol = Depends(get_create_ct_shop_use_case)
) -> CityTradingShopResponseSchema:
    return await use_case(user)

@router.post('/city-shop/{id}/renewal', response_model=CityTradingShopReadSchema)
async def renewal_licence_city_shop(
    id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateLicenseCTShopUseCaseProtocol = Depends(get_update_license_duration_ct_shop_use_case)
) -> CityTradingShopReadSchema:
    return await use_case(id, user)

@router.patch('/city-shop/{id}/info', response_model=CityTradingShopReadSchema)
async def update_info_city_shop(
    city_info: CityTradingShopUpdateInfoSchema,
    id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateInfoCTShopUseCaseProtocol = Depends(get_update_info_ct_shop_use_case)
) -> CityTradingShopReadSchema:
    return await use_case(id, city_info, user)

@router.patch('/city-shop/{id}/photo', response_model=CityTradingShopReadSchema)
async def update_photo_city_shop(
    photo: CityTradingShopUpdatePhotoSchema,
    id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdatePhotoCTShopUseCaseProtocol = Depends(get_update_photo_ct_shop_use_case)
) -> CityTradingShopReadSchema:
    return await use_case(id, photo, user)


@router.post('/city-shop/{id}/logo', response_model=CityTradingShopReadSchema)
async def upload_city_shop_logo(
    id: uuid.UUID = Path(...),
    request: Request = ...,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdatePhotoCTShopUseCaseProtocol = Depends(get_update_photo_ct_shop_use_case)
) -> CityTradingShopReadSchema:
    # Используем upload через file-storage by-service
    form = await request.form()   
    file = form.get('file')

    # Подготавливаем payload для file service
    file_payload = {
        "template_name": "city_shop_logo",
        "filename": getattr(file, 'filename', 'logo')
    }

    # Валидируем размер логотипа (ожидается 120x90)
    file_content = await file.read()
    try:
        img = Image.open(BytesIO(file_content))
        img.verify()
        img = Image.open(BytesIO(file_content))
        width, height = img.size
    except Exception:
        raise ValidationError(field='file', message='Invalid image file')

    if (width, height) != (120, 90):
        raise ValidationError(field='file', message='Invalid logo size. Expected 120x90')

    # Загружаем файл в file-service
    file_service = get_file_service_client()
    # передаём байты и filename через payload
    file_payload.update({"filename": getattr(file, 'filename', 'logo'), "content_type": getattr(file, 'content_type', 'application/octet-stream')})
    file_resp = await file_service.create_by_service(file_payload, file_content, user.character_id)

    # Обновляем фото/лого магазина
    photo_schema = CityTradingShopUpdatePhotoSchema(photo_id=file_resp.id)
    return await use_case(id, photo_schema, user)


@router.post('/city-shop/level-up', response_model=CityTradingShopResponseSchema)
async def level_up_city_shop(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: LevelUpCTShopUseCaseProtocol = Depends(get_level_up_ct_shop_use_case)
) -> CityTradingShopResponseSchema:
    return await use_case(user)


@router.post('/city-shop/{id}/upgrade', response_model=CityTradingShopResponseSchema)
async def upgrade_city_shop(
    id: uuid.UUID = Path(...),
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpgradeCTShopUseCaseProtocol = Depends(get_upgrade_ct_shop_use_case)
) -> CityTradingShopResponseSchema:
    if not user.character_id:
        raise PermissionDeniedError()
    return await use_case(id, user.character_id)


@router.get('/me', response_model=list[InventoryItemReadSchema])
async def get_character_items(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetCharacterItemsUseCaseProtocol = Depends(get_get_character_items_use_case)
) -> list[InventoryItemReadSchema]:
    return await use_case(user)

@router.get('/from-location', response_model=LocationItemsGroupedSchema)
async def get_items_from_location(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetItemsFromLocationUseCaseProtocol = Depends(get_get_items_from_location_use_case)
) -> LocationItemsGroupedSchema:
    return await use_case(user)


