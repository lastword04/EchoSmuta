import uuid
from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import Optional
from shared.schemas.base import CreateBaseModel, UpdateBaseModel, TimestampMixin
from shared.schemas.characters import CharacterSimpleInfoListReadSchema

class CategoryBaseSchema(BaseModel):
    name: str = Field(..., description="The name of category")

class CategoryCreateSchema(CategoryBaseSchema, CreateBaseModel):
    pass

class CategoryCreateDBSchema(CategoryCreateSchema):
    owner_character_id: uuid.UUID = Field(..., description="Owner category character")
    is_main: bool = Field(..., description="Is main category?")
    max_count_characters: int = Field(..., description="Max count characters in this group") 

    is_send_notifications: Optional[bool] = Field(None, description="Can this group send notifications")
    is_receive_notifications: Optional[bool] = Field(None, description="Can this group recieve notifications")
    is_block_send_mails: bool = Field(False, description="Can this group send mails")

    @model_validator(mode='after')
    def validate_notifications_for_non_main(self):
        if not self.is_main:
            if self.is_send_notifications is not None:
                raise ValidationError('is_send_notifications must be None if is_main is False')
            if self.is_receive_notifications is not None:
                raise ValidationError('is_receive_notifications must be None if is_main is False')
        return self 
    

class CategoryUpdateCheckbox(BaseModel):
    is_send_notifications: Optional[bool] = Field(None, description="Can this group send notifications")
    is_receive_notifications: Optional[bool] = Field(None, description="Can this group recieve notifications")
    is_block_send_mails: bool = Field(False, description="Can this group send mails")

class CategoryUpdateSchema(CategoryBaseSchema, UpdateBaseModel):
    pass

class CategoryReadSchema(CategoryBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Id of category")
    owner_character_id: uuid.UUID = Field(..., description="Owner category character")
    is_main: bool = Field(..., description="Is main category?")
    max_count_characters: int = Field(..., description="Max count characters in this group") 

class CategoryWithCharacterIdsReadSchema(CategoryBaseSchema):
    id: uuid.UUID = Field(..., description="Id of category")
    characters_ids: list[uuid.UUID] = Field(..., description="Id all characters in group")
    
class CategoryWithCharactersReadSchema(CategoryBaseSchema, CharacterSimpleInfoListReadSchema):
    id: uuid.UUID = Field(..., description="Id of category")

class CategoryWithCharacterCountSchema(CategoryReadSchema):
    characters_count: int = 0
    is_send_notifications: Optional[bool] = Field(None, description="Can this group send notifications")
    is_receive_notifications: Optional[bool] = Field(None, description="Can this group recieve notifications")
    is_block_send_mails: bool = Field(False, description="Can this group send mails")

class CategoryCharacterBaseSchema(BaseModel):
    character_id: uuid.UUID = Field(..., description="Character id for chategory")
    category_id: uuid.UUID = Field(..., description="Category id")

class CategoryCharacterCreateSchema(CategoryCharacterBaseSchema, CreateBaseModel):
    pass

class CategoryCharacterUpdateSchema(CategoryCharacterBaseSchema, UpdateBaseModel):
    pass

class CategoryCharacterReadSchema(CategoryCharacterBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Id of category character ")
