import uuid
from pydantic import BaseModel, Field
from .base import TimestampMixin
from ..enums import LocationType

class LocationBaseSchema(BaseModel):
    name: str = Field(..., max_length=128, description="Name of the location")
    slug: str = Field(..., max_length=128, description="Unique slug for the location")
    city_id: uuid.UUID = Field(..., description="ID of the city the location belongs to")
    type: LocationType = Field(..., description="Type of the location")
    serial_number: int = Field(..., description="Serial number of the location")

class LocationReadSchema(LocationBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the location")
