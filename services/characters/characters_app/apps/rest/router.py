import uuid
from fastapi import APIRouter, Depends
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .schemas import (
    RentRoomRequestSchema, RestRentalReadSchema, RestStatusResponseSchema,
    EnterHouseRequestSchema, HouseReadSchema, HousesStatusResponseSchema,
    InstallFurnitureRequestSchema, UninstallFurnitureRequestSchema, HouseFurnitureItemSchema,
    UpdateHouseWallpaperSchema, FurnitureMoveResponseSchema,
    KnockRequestSchema, HouseGuestsResponseSchema, GuestActionResponseSchema,
    CurrentHouseReadSchema
)
from .use_cases.rent_room import RentRoomUseCaseProtocol
from .use_cases.exit_room import ExitRoomUseCaseProtocol
from .use_cases.enter_room import EnterRoomUseCaseProtocol
from .use_cases.get_status import GetRestStatusUseCaseProtocol
from .use_cases.sync_expiry import SyncExpiryUseCaseProtocol
from .use_cases.buy_house import BuyHouseUseCaseProtocol
from .use_cases.enter_house import EnterHouseUseCaseProtocol
from .use_cases.exit_house import ExitHouseUseCaseProtocol
from .use_cases.get_house_status import GetHouseStatusUseCaseProtocol
from .use_cases.install_furniture import InstallFurnitureUseCaseProtocol
from .use_cases.uninstall_furniture import UninstallFurnitureUseCaseProtocol
from .use_cases.get_house_furniture import GetHouseFurnitureUseCaseProtocol
from .use_cases.get_my_furniture import GetMyFurnitureUseCaseProtocol
from .use_cases.update_house_wallpaper import UpdateHouseWallpaperUseCaseProtocol
from .use_cases.knock_house import KnockHouseUseCaseProtocol
from .use_cases.accept_guest_request import AcceptGuestRequestUseCaseProtocol
from .use_cases.reject_guest_request import RejectGuestRequestUseCaseProtocol
from .use_cases.kick_house_guest import KickHouseGuestUseCaseProtocol
from .use_cases.get_house_guests import GetHouseGuestsUseCase, GetHouseGuestsUseCaseProtocol
from .depends import (
    get_rent_room_use_case,
    get_exit_room_use_case,
    get_enter_room_use_case,
    get_rest_status_use_case,
    get_sync_expiry_use_case,
    get_buy_house_use_case,
    get_enter_house_use_case,
    get_exit_house_use_case,
    get_house_status_use_case,
    get_install_furniture_use_case, 
    get_uninstall_furniture_use_case, 
    get_house_furniture_use_case,
    get_my_furniture_use_case,
    get_update_house_wallpaper_use_case,
    get_knock_house_use_case,
    get_accept_guest_request_use_case,
    get_reject_guest_request_use_case,
    get_kick_house_guest_use_case,
    get_house_guests_use_case,
)

router = APIRouter(prefix="/api/rest", tags=["Rest"])


@router.post("/rent", response_model=RestRentalReadSchema)
async def rent_room(
    data: RentRoomRequestSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: RentRoomUseCaseProtocol = Depends(get_rent_room_use_case),
) -> RestRentalReadSchema:
    return await use_case(user=user, days=data.days)


@router.post("/exit")
async def exit_room(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ExitRoomUseCaseProtocol = Depends(get_exit_room_use_case),
) -> None:
    await use_case(user=user)


@router.post("/enter")
async def enter_room(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: EnterRoomUseCaseProtocol = Depends(get_enter_room_use_case),
) -> None:
    await use_case(user=user)


@router.get("/status", response_model=RestStatusResponseSchema)
async def get_rest_status(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetRestStatusUseCaseProtocol = Depends(get_rest_status_use_case),
) -> RestStatusResponseSchema:
    return await use_case(user=user)


@router.post("/sync-expiry")
async def sync_expiry(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: SyncExpiryUseCaseProtocol = Depends(get_sync_expiry_use_case),
) -> dict:
    return await use_case(user=user)



houses_router = APIRouter(prefix="/api/houses", tags=["Houses"])


@houses_router.post("/buy", response_model=HouseReadSchema)
async def buy_house(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: BuyHouseUseCaseProtocol = Depends(get_buy_house_use_case),
) -> HouseReadSchema:
    return await use_case(user=user)


@houses_router.post("/enter", response_model=CurrentHouseReadSchema)
async def enter_house(
    data: EnterHouseRequestSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: EnterHouseUseCaseProtocol = Depends(get_enter_house_use_case),
) -> CurrentHouseReadSchema:
    return await use_case(user=user, house_id=data.house_id)


@houses_router.post("/exit")
async def exit_house(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: ExitHouseUseCaseProtocol = Depends(get_exit_house_use_case),
) -> None:
    await use_case(user=user)


@houses_router.get("/status", response_model=HousesStatusResponseSchema)
async def get_houses_status(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetHouseStatusUseCaseProtocol = Depends(get_house_status_use_case),
) -> HousesStatusResponseSchema:
    return await use_case(user=user)


@houses_router.post("/install-furniture", response_model=FurnitureMoveResponseSchema)
async def install_furniture(
    data: InstallFurnitureRequestSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: InstallFurnitureUseCaseProtocol = Depends(get_install_furniture_use_case),
) -> FurnitureMoveResponseSchema:
    return await use_case(user=user, house_id=data.house_id, inventory_item_id=data.inventory_item_id)


@houses_router.post("/uninstall-furniture", response_model=FurnitureMoveResponseSchema)
async def uninstall_furniture(
    data: UninstallFurnitureRequestSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UninstallFurnitureUseCaseProtocol = Depends(get_uninstall_furniture_use_case),
) -> FurnitureMoveResponseSchema:
    return await use_case(user=user, inventory_item_id=data.inventory_item_id)


@houses_router.get("/{house_id}/furniture", response_model=list[HouseFurnitureItemSchema])
async def get_house_furniture(
    house_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetHouseFurnitureUseCaseProtocol = Depends(get_house_furniture_use_case),
) -> list[HouseFurnitureItemSchema]:
    return await use_case(user=user, house_id=house_id)


@houses_router.get("/furniture", response_model=list[HouseFurnitureItemSchema])
async def get_my_furniture(
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMyFurnitureUseCaseProtocol = Depends(get_my_furniture_use_case),
) -> list[HouseFurnitureItemSchema]:
    return await use_case(user=user)


@houses_router.patch("/{house_id}/wallpaper")
async def update_house_wallpaper(
    house_id: uuid.UUID,
    data: UpdateHouseWallpaperSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateHouseWallpaperUseCaseProtocol = Depends(get_update_house_wallpaper_use_case),
) -> None:
    await use_case(user=user, house_id=house_id, wallpaper_photo_id=data.wallpaper_photo_id)


@houses_router.post("/knock")
async def knock_house(
    data: KnockRequestSchema,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: KnockHouseUseCaseProtocol = Depends(get_knock_house_use_case),
) -> None:
    await use_case(user=user, house_number=data.house_number)


@houses_router.get("/{house_id}/guests", response_model=HouseGuestsResponseSchema)
async def get_house_guests(
    house_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetHouseGuestsUseCaseProtocol = Depends(get_house_guests_use_case),
) -> HouseGuestsResponseSchema:
    return await use_case(user=user, house_id=house_id)


@houses_router.post("/guest-requests/{request_id}/accept", response_model=GuestActionResponseSchema)
async def accept_guest_request(
    request_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: AcceptGuestRequestUseCaseProtocol = Depends(get_accept_guest_request_use_case),
) -> GuestActionResponseSchema:
    return await use_case(user=user, request_id=request_id)


@houses_router.post("/guest-requests/{request_id}/reject", response_model=GuestActionResponseSchema)
async def reject_guest_request(
    request_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: RejectGuestRequestUseCaseProtocol = Depends(get_reject_guest_request_use_case),
) -> GuestActionResponseSchema:
    return await use_case(user=user, request_id=request_id)


@houses_router.post("/guests/{character_id}/kick", response_model=GuestActionResponseSchema)
async def kick_house_guest(
    character_id: uuid.UUID,
    user: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: KickHouseGuestUseCaseProtocol = Depends(get_kick_house_guest_use_case),
) -> GuestActionResponseSchema:
    return await use_case(user=user, guest_character_id=character_id)