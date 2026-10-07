import uuid
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from typing_extensions import Self
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin
from .enums import MenuItem
from .exceptions import DuplicateMenuItemsError

class CharacterFastItemBaseSchema(BaseModel):
    first_item: Optional[MenuItem] = Field(None, description="First pin menu item for character")
    second_item: Optional[MenuItem] = Field(None, description="Second pin menu item for character")

    @model_validator(mode='after')
    def validate_items_are_different(self: Self) -> Self:
        if self.first_item is not None and self.second_item is not None:
            if self.first_item == self.second_item:
                raise DuplicateMenuItemsError(self.first_item, self.second_item)
        return self

class CharacterFastItemBaseDBSchema(CharacterFastItemBaseSchema):
    character_id: uuid.UUID = Field(..., description="Id character for fast panel")

class CharacterFastItemCreateSchema(CharacterFastItemBaseSchema, CreateBaseModel):
    pass

class CharacterFastItemCreateDBSchema(CharacterFastItemBaseDBSchema, CreateBaseModel):
    pass


class CharacterFastItemUpdateSchema(CharacterFastItemBaseSchema, CreateBaseModel):
    pass

class CharacterFastItemUpdateDBSchema(CharacterFastItemBaseDBSchema, UpdateBaseModel):
    pass

class CharacterFastItemReadSchema(CharacterFastItemBaseDBSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique id for fast item")