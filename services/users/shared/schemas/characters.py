from datetime import datetime
from decimal import Decimal
import re
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from .base import TimestampMixin, PaginationResultSchema
from .locations import LocationReadSchema
from ..enums import Race

class CharacterBaseSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=21, description="Name of the character")
    user_id: uuid.UUID = Field(..., description="ID of the user who owns the character")
    location_slug: Optional[str] = Field(None, description="Location of the character")
    is_male: bool = Field(..., description="Gender of the character")
    race: Race = Field(..., description="Race of the character")
    level: int = Field(..., description="Level of the character")
    experience: int = Field(..., description="Experience points of the character")
    health: float = Field(..., description="Health points of the character")
    max_health: float = Field(..., description="Max health points of the character")
    tiredness: float = Field(..., description="Tiredness points of the character")
    max_tiredness: float = Field(..., description="Max tiredness points of the character")
    endurance: int = Field(..., description="Endurance points of the character")
    mana: float = Field(..., description="Mana points of the character")
    max_mana: float = Field(..., description="Max mana points of the character")
    intelligence: int = Field(..., description="Intelligence points of the character")
    weight: int = Field(..., description="Weight points of the character")
    max_weight: int = Field(..., description="Max weight points of the character")
    gold: Decimal = Field(..., description="Gold owned by the character")
    ducats: Decimal = Field(..., description="Ducats owned by the character")
    power: int = Field(..., description="Power of the character")
    agility: int = Field(..., description="Agility of the character")
    lucky: int = Field(..., description="Luck of the character")
    is_main: bool = Field(..., description="Is the character the main character?")
    photo_id: uuid.UUID = Field(..., description="ID of the photo character")
    is_online: bool = Field(False, description="Status of character")
    is_active: bool = Field(True, description="Is the character active?")
    deactivated_at: Optional[datetime] = Field(None, description="Timestamp when the character was deactivated")
    scheduled_deletion_at: Optional[datetime] = Field(None, description="Timestamp when the character is scheduled for deletion")
    mastership_sword: int = Field(0, description="Mastership of the sword")
    mastership_axe: int = Field(0, description="Mastership of the axe")
    mastership_hammer: int = Field(0, description="Mastership of the hammer")    
    equipment_bonuses: dict = Field(default_factory=dict, description="Equipment bonuses from equipped items")      
    food_cooldown_until: Optional[datetime] = None
    rest_state: Optional[str] = Field(None, description="Rest state: entrance, inside, or None")
    current_house_id: Optional[uuid.UUID] = Field(None, description="ID дома, в котором сейчас находится персонаж")
    current_room_id: Optional[str] = Field(None, description="Виртуальная комната для чата (house:uuid, inn:inside)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        # Проверка длины
        if len(v) < 2 or len(v) > 21:
            raise ValueError('Name must be more 2 characters and no more than 21 characters long')
        
        # Проверка на пустоту (с учетом пробелов)
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Проверка на допустимые символы (добавлен пробел)
        if not re.match(r'^[a-zA-Z0-9 ]+$|^[а-яА-ЯёЁ0-9 ]+$', v):
            raise ValueError('Name must contain only letters of one language (Russian or English), numbers and spaces')
        
        # Проверка, что все буквы одного языка
        has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', v))
        has_latin = bool(re.search(r'[a-zA-Z]', v))
        
        if has_cyrillic and has_latin:
            raise ValueError('Name must contain letters of only one language (Russian or English)')
        
        # Проверка на пробелы в начале/конце
        if v != v.strip():
            raise ValueError('Name cannot start or end with a space')
        
        # Проверка на множественные пробелы подряд
        if '  ' in v:
            raise ValueError('Name cannot contain multiple consecutive spaces')
        
        return v


class CharacterMultCreateSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the character")
    race: Race = Field(..., description="Race of the character")
    is_male: bool = Field(..., description="Gender of the character")


class CharacterCreateSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the character")
    user_id: uuid.UUID = Field(..., description="ID of the user who owns the character")
    race: Race = Field(..., description="Race of the character")
    is_male: bool = Field(..., description="Gender of the character")
    referral_code: Optional[str] = Field(None, description="Referral code for the character")

class CharacterReadSchema(CharacterBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    equipment_bonuses: dict = Field(default_factory=dict, description="Equipment bonuses")
    effective_power: int | None = Field(default=None, description="Сила с учётом всех модификаторов")
    effective_agility: int | None = Field(default=None, description="Ловкость с учётом всех модификаторов")
    effective_lucky: int | None = Field(default=None, description="Удача с учётом всех модификаторов")
    effective_max_health: float | None = Field(default=None, description="Макс. здоровье с учётом всех модификаторов")
    effective_max_mana: float | None = Field(default=None, description="Макс. мана с учётом всех модификаторов")
    effective_max_tiredness: float | None = Field(default=None, description="Макс. усталость с учётом всех модификаторов")
    
    @field_validator('health', 'max_health', 'mana', 'max_mana', mode='before')
    @classmethod
    def round_stats(cls, v):
        """Округляем статы до целых для отображения на фронтенде"""
        if v is not None:
            return int(round(float(v)))
        return v

class CharacterUpdateSchema(CharacterBaseSchema):
    pass

class CharacterSimpleReadSchema(TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    name: str = Field(..., max_length=100, description="Name of the character")
    user_id: uuid.UUID = Field(..., description="ID of the user who owns the character")
    is_main: bool = Field(..., description="Is the character the main character?")
    is_online: bool = Field(False, description="Status of character")
    is_active: bool = Field(True, description="Is the character active?")  
    is_banned: bool = Field(False, description="Is the character banned?")  


class CharacterSimpleListReadSchema(BaseModel):
    characters: list[CharacterSimpleReadSchema] = Field(..., description="List of simple character data")

class CharacterListIds(BaseModel):
    ids: list[uuid.UUID] = Field(..., description="List of character IDs")

class CharacterIdsResponse(BaseModel):
    """Ответ с списком ID персонажей"""
    ids: list[uuid.UUID]  

class UserListids(BaseModel):
    ids: list[uuid.UUID] = Field(..., description="List of user IDs")


class CharacterSimpleInfoReadSchema(TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    name: str = Field(..., max_length=100, description="Name of the character")
    is_male: bool = Field(..., description="Gender of character")
    race: Race = Field(..., description="Race of character")
    level: int = Field(..., description="Level of character")
    is_online: bool = Field(False, description="Status of character")
    location_slug: Optional[str] = Field(None, description="Location of the character")
    current_room_id: Optional[str] = Field(None, description="Виртуальная комната (house:uuid, inn:inside)")

class CharacterMiningStats(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    name: str = Field(..., max_length=100, description="Name of the character")
    level: int = Field(..., description="Level of character")
    health: float = Field(..., description="Health points of the character")
    max_health: float = Field(..., description="Max health points of the character")
    tiredness: float = Field(..., description="Tiredness points of the character")
    strength: Optional[int] = Field(default=0, description="Strength points of the character (default 0 if missing)")
    agility: Optional[int] = Field(default=0, description="Agility points of the character (default 0 if missing)")
    luck: Optional[int] = Field(default=0, description="Luck points of the character (default 0 if missing)")
    is_online: bool = Field(False, description="Status of character")
    location_slug: Optional[str] = Field(None, description="Location of the character")

    @field_validator('health', 'max_health', mode='before')
    @classmethod
    def round_stats(cls, v):
        """Округляем статы до целых для отображения на фронтенде"""
        if v is not None:
            return int(round(float(v)))
        return v

class CharacterItemsBalance(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    name: str = Field(..., max_length=100, description="Name of the character")
    level: int = Field(..., description="Level of character")
    is_online: bool = Field(False, description="Status of character")
    location_slug: Optional[str] = Field(None, description="Location of the character")
    ducats: Decimal = Field(..., description="Ducats owned by the character")


class CharacterWeightBalance(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the character")
    name: str = Field(..., max_length=100, description="Name of the character")
    level: int = Field(..., description="Level of character")
    is_online: bool = Field(False, description="Status of character")
    location_slug: Optional[str] = Field(None, description="Location of the character")
    weight: int = Field(..., description="Current weight of the character")
    max_weight: int = Field(..., description="Max weight of the character")


class CharacterSimpleInfoListReadSchema(BaseModel):
    characters: list[CharacterSimpleInfoReadSchema]

class PaginationCharacterSimpleInfoReadSchema(PaginationResultSchema[CharacterSimpleInfoReadSchema]):
    pass

class CharacterOnlineStatus(BaseModel):
    is_online: bool

class TirednessStat(BaseModel):
    tiredness: float

class DucatsStat(BaseModel):
    ducats: Decimal

class WeightStat(BaseModel):
    weight: float

class CharacterChangeLocationEvent(BaseModel):
    character_id: uuid.UUID
    old_location: LocationReadSchema
    new_location: LocationReadSchema
    name: Optional[str] = None
    level: Optional[int] = None
    race: Optional[str] = None

class CharacterCurrencyOperationResponse(BaseModel):
    """Ответ на операцию debit/credit валюты персонажа (internal ledger)."""
    character_id: uuid.UUID
    operation_id: uuid.UUID
    amount: Decimal
    operation_type: str
    currency: str
    balance_after: Decimal

    model_config = ConfigDict(from_attributes=True)

class CharacterOnlineStatusChangedEvent(BaseModel):
    character_id: uuid.UUID
    is_online: bool
    location_slug: Optional[str] = None
    current_room_id: Optional[str] = None
    name: Optional[str] = None
    level: Optional[int] = None
    race: Optional[str] = None