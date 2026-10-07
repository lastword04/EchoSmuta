import uuid
from enum import Enum

from pydantic import BaseModel, Field


class ItemMessageScope(str, Enum):
    PRIVATE = "private"
    CITY = "city"


class ItemMessageEventSchema(BaseModel):
    event_type: str = Field(..., description="Domain event type for item system message")
    character_id: uuid.UUID | None = Field(None, description="Actor character id")
    location_slug: str = Field(..., description="Location slug related to the event")
    content: str = Field(..., description="Rendered system message content")
    scope: ItemMessageScope = Field(..., description="How the message should be delivered in chat")
    target_user_ids: list[uuid.UUID] | None = Field(
        None,
        description="Explicit recipients for targeted messages",
    )
    is_trade: bool = Field(False, description="Whether this message should be filtered as trade")
