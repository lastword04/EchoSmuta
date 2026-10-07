import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from shared.enums import ResultStatus
from shared.schemas.base import CreateBaseModel, TimestampMixin, UpdateBaseModel

from .enums import MiningStatus


class CharacterResourceOperationRequest(BaseModel):
    operation_id: uuid.UUID
    amount: int = Field(..., gt=0)


class CharacterResourceOperationResponse(BaseModel):
    character_id: uuid.UUID
    resource_slug: str
    operation_id: uuid.UUID
    operation_type: str
    amount: int
    balance_after: int


class CharacterResourcesResponse(BaseModel):
    character_id: uuid.UUID
    resources: list["ResourseCharacterResponse"]


class ResourceBaseSchema(BaseModel):
    name: str = Field(..., max_length=128)
    slug: str = Field(..., max_length=128)
    category: str | None = Field(None, max_length=32)
    weight: int = Field(...)
    price: int = Field(...)
    serial_number: int = Field(...)

class ResourceCreateSchema(ResourceBaseSchema, CreateBaseModel):
    pass


class ResourceUpdateSchema(ResourceBaseSchema, UpdateBaseModel):
    pass

class ResourceReadSchema(ResourceBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)

class LocationResourceBaseSchema(BaseModel):
    location_slug: str = Field(..., max_length=128)
    resource_slug: str = Field(..., max_length=100)
    chance: float
    experience_on_resource: int = 0
    current_amount: int = 0
    max_amount: int = 0

class LocationResourceCreateSchema(LocationResourceBaseSchema, CreateBaseModel):
    pass

class LocationResourceUpdateSchema(LocationResourceBaseSchema, UpdateBaseModel):
    pass

class LocationResourceReadSchema(LocationResourceBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)


class CharacterLocationStatsBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(...)
    location_slug: str = Field(..., max_length=128)
    experience: int = 0
    level: int = 1
    add_chance: float = 0.0

class CharacterLocationStatsCreateSchema(CharacterLocationStatsBaseSchema, CreateBaseModel):
    pass

class CharacterLocationStatsUpdateSchema(CharacterLocationStatsBaseSchema, UpdateBaseModel):
    pass

class CharacterLocationStatsReadSchema(CharacterLocationStatsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)

class CharacterResourceBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(...)
    resource_slug: str = Field(..., max_length=128)
    amount: int = 0

class CharacterResourceCreateSchema(CharacterResourceBaseSchema, CreateBaseModel):
    pass

class CharacterResourceUpdateSchema(CharacterResourceBaseSchema, UpdateBaseModel):
    pass

class CharacterResourceReadSchema(CharacterResourceBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)


# Response

class ResourseCharacterResponse(BaseModel):
    resource_name: str
    resource_slug: str
    amount: int
    available_amount: int | None = None 

class LocationResourceWithAmount(BaseModel):
    resource_name: str
    resource_slug: str
    chance: float
    current_amount: int
    amount: int

class LocationResourcePublic(BaseModel):
    resource_name: str
    resource_slug: str
    chance: float
    current_amount: int
    experience_on_resource: int


class LocationResourcesAndCharacterStats(BaseModel):
    resources: list[LocationResourceWithAmount]
    character_location_level: CharacterLocationStatsReadSchema


class ExperienceForLevelBaseSchema(BaseModel):
    experience: int
    level: int
    success_rate_one: float = 0.0
    success_rate_two: float = 0.0
    success_rate_three: float = 0.0


class ExperienceForLevelCreateSchema(ExperienceForLevelBaseSchema, CreateBaseModel):
    pass

class ExperienceForLevelUpdateSchema(ExperienceForLevelBaseSchema, UpdateBaseModel):
    pass

class ExperienceForLevelReadSchema(ExperienceForLevelBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)


class LocationSettingsBaseSchema(BaseModel):
    location_slug: str = Field(..., max_length=128)
    up_chance_for_unluck: float = 0.0

class LocationSettingsCreateSchema(LocationSettingsBaseSchema, CreateBaseModel):
    pass

class LocationSettingsUpdateSchema(LocationSettingsBaseSchema, UpdateBaseModel):
    pass

class LocationSettingsReadSchema(LocationSettingsBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)


class MiningActionBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(...)
    location_slug: str = Field(..., max_length=128)
    start_time: datetime
    finish_time: datetime
    message: str
    status: MiningStatus = MiningStatus.IN_PROGRESS
    celery_task_id: str | None = None
    result_status: ResultStatus | None = None
    recived_resourse_slug: str | None = None
    count_recived_resource: int | None = None


class MiningActionCreateSchema(MiningActionBaseSchema, CreateBaseModel):
    pass

class MiningActionUpdateSchema(MiningActionBaseSchema, UpdateBaseModel):
    pass

class MiningActionReadSchema(MiningActionBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(...)

class MiningActionResponseSchema(BaseModel):
    id: uuid.UUID | None = None
    status: MiningStatus
    location_slug: str | None = None
    remaining_time_seconds: int | None = None
    message: str | None = None
    finish_time: datetime | None = None

class MonsterLocationBaseSchema(BaseModel):
    location_slug: str = Field(..., max_length=128)
    standart_monster_name: str = Field(..., max_length=128)
    standart_monster_skin_slug: str = Field(..., max_length=128)
    improved_monster_name: str = Field(..., max_length=128)
    improved_monster_skin_slug: str = Field(..., max_length=128)

class MonsterLocationCreateSchema(MonsterLocationBaseSchema, CreateBaseModel):
    pass

class MonsterLocationUpdateSchema(MonsterLocationBaseSchema, UpdateBaseModel):
    pass

class MonsterLocationReadSchema(MonsterLocationUpdateSchema, TimestampMixin):
    id: uuid.UUID = Field(...)
