from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DealEventType(str, Enum):
    CREATED = "deal_created"
    ACCEPTED = "deal_accepted"
    UPDATED = "deal_updated"
    CONFIRMED = "deal_confirmed"
    COMPLETED = "deal_completed"
    CANCELLED = "deal_cancelled"
    EXPIRED = "deal_expired"


class DealEventSchema(BaseModel):
    event_type: DealEventType
    deal_id: UUID
    character_id: UUID
    initiator_character_id: Optional[UUID] = None
    partner_character_id: Optional[UUID] = None
    location_slug: Optional[str] = None
    details: Optional[dict] = None
    system_messages: Optional[list[dict]] = None 