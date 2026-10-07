import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RentRoomRequestSchema(BaseModel):
    days: int


class RestRentalReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_number: int
    days: int
    rented_at: datetime
    expires_at: datetime


class RestStatusResponseSchema(BaseModel):
    location_slug: Optional[str]
    rest_state: Optional[str]
    has_active_rental: bool
    room_number: Optional[int]
    expires_at: Optional[datetime]
    days: Optional[int]
    prices: dict[str, str]
    max_rooms: int
    available_rooms: int


class EnterHouseRequestSchema(BaseModel):
    house_id: uuid.UUID


class HouseReadSchema(BaseModel):
    id: uuid.UUID
    number: int
    capacity: int
    current_volume: int
    bonuses: dict[str, float]
    wallpaper_photo_id: uuid.UUID | None = None
    furniture: list[dict] = []
    guests_count: int = 0
    guests: list[dict] = []


class KnockRequestSchema(BaseModel):
    house_number: int


class HouseGuestReadSchema(BaseModel):
    character_id: uuid.UUID
    name: str


class HouseGuestRequestReadSchema(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    name: str
    expires_at: datetime


class HouseGuestsResponseSchema(BaseModel):
    guests: list[HouseGuestReadSchema]
    requests: list[HouseGuestRequestReadSchema]


class CurrentHouseReadSchema(BaseModel):
    id: uuid.UUID
    number: int
    capacity: int
    current_volume: int
    bonuses: dict[str, float]
    wallpaper_photo_id: uuid.UUID | None = None
    furniture: list[dict] = []
    is_owner: bool
    owner_name: str
    guests_count: int
    guests: list[dict] = []


class HousesStatusResponseSchema(BaseModel):
    location_slug: str | None
    current_house_id: uuid.UUID | None
    house_price: str
    max_guests: int
    houses: list[HouseReadSchema]
    current_house: CurrentHouseReadSchema | None = None


class InstallFurnitureRequestSchema(BaseModel):
    house_id: uuid.UUID
    inventory_item_id: uuid.UUID


class UninstallFurnitureRequestSchema(BaseModel):
    inventory_item_id: uuid.UUID


class HouseFurnitureItemSchema(BaseModel):
    house_id: uuid.UUID | None = None
    inventory_item_id: uuid.UUID
    slug: str
    wear: int
    max_wear: int | None = None
    volume: int | None = None
    weight: int
    ability_parameters: dict | None = None
    name: str


class UpdateHouseWallpaperSchema(BaseModel):
    wallpaper_photo_id: uuid.UUID | None
    

class FurnitureMoveResponseSchema(BaseModel):
    house_id: uuid.UUID
    my_furniture: list[HouseFurnitureItemSchema]
    house_furniture: list[HouseFurnitureItemSchema]   
    house: HouseReadSchema


class GuestActionResponseSchema(BaseModel):
    house: CurrentHouseReadSchema
    requests: list[HouseGuestRequestReadSchema]
