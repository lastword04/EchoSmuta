import datetime
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from shared.schemas.base import (
    CreateBaseModel, UpdateBaseModel, TimestampMixin, 
    PaginationResultSchema
)
from shared.schemas.files import FileReadSchema as FileWithUrlReadSchema
from .enums import ForumSection

class ForumBaseSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the forum")
    section: ForumSection = Field(..., description="Section of the forum")
    

class ForumCreateDBSchema(ForumBaseSchema, CreateBaseModel):
    pass

class ForumUpdateDBSchema(ForumBaseSchema, UpdateBaseModel):
    pass

class ForumReadSchema(ForumBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the forum")
    last_comment_user_id: Optional[uuid.UUID] = Field(
        None, description="ID of the user who made the last comment"
    )
    last_comment_datetime: Optional[datetime.datetime] = Field(
        None, description="Datetime of the last comment"
    )
    class Config:
        from_attributes = True

class ForumWithCharacterNameReadSchema(ForumReadSchema, TimestampMixin):

    last_comment_character_name: Optional[str] = Field(
        None, description="Name of the character who made the last comment"
    )

    class Config:
        from_attributes = True


class ForumWithStats(BaseModel):
    forum: ForumReadSchema = Field(..., description="Forum details")
    comments_count: int = Field(..., description="Total number of comments in the forum")
    topics_count: int = Field(..., description="Total number of characters in the forum")

class ForumWithStatsAndCharacterNames(BaseModel):
    forum: ForumWithCharacterNameReadSchema = Field(..., description="Forum details with character names")
    comments_count: int = Field(..., description="Total number of comments in the forum")
    topics_count: int = Field(..., description="Total number of characters in the forum")


class TopicSimpleBaseSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the topic")
    forum_id: uuid.UUID = Field(..., description="ID of the forum to which the topic belongs")
    views: int = Field(0, description="Number of views of the topic")

class TopicRequestSchema(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the topic")

class TopicCreateSchema(TopicRequestSchema):
    pass

class TopicUpdateSchema(TopicRequestSchema):
    pass


class TopicCreateDBSchema(TopicSimpleBaseSchema, CreateBaseModel):
    last_comment_user_id: Optional[uuid.UUID] = Field(
        None, description="ID of the user who made the last comment in the topic"
    )
    last_comment_datetime: Optional[datetime.datetime] = Field(
        None, description="Datetime of the last comment in the topic"
    )
    author_user_id: uuid.UUID = Field(..., description="ID of the user who created the topic")


class TopicUpdateDBSchema(TopicSimpleBaseSchema, UpdateBaseModel):
    last_comment_user_id: Optional[uuid.UUID] = Field(
        None, description="ID of the user who made the last comment in the topic"
    )
    last_comment_datetime: Optional[datetime.datetime] = Field(
        None, description="Datetime of the last comment in the topic"
    )
    author_user_id: uuid.UUID = Field(..., description="ID of the user who created the topic")


class TopicReadSchema(TopicSimpleBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the topic")
    last_comment_datetime: Optional[datetime.datetime] = Field(
        None, description="Datetime of the last comment in the topic"
    )
    last_comment_user_id: Optional[uuid.UUID] = Field(
        None, description="ID of the user who made the last comment in the topic"
    )
    author_user_id: uuid.UUID = Field(..., description="ID of the user who created the topic")


    class Config:
        from_attributes = True


class TopicReadWithCharacterNameSchema(TopicReadSchema):
    author_character_name: Optional[str] = Field(
        None, description="Name of the character who created the topic"
    )
    last_comment_character_name: Optional[str] = Field(
        None, description="Name of the character who made the last comment in the topic"
    )

    class Config:
        from_attributes = True


class TopicWithStats(BaseModel):
    topic: TopicReadSchema = Field(..., description="Topic details")
    comments_count: int = Field(..., description="Total number of comments in the topic")


class TopicWithStatsAndCharacterNames(BaseModel):
    topic: TopicReadWithCharacterNameSchema = Field(..., description="Topic details with character names")
    comments_count: int = Field(..., description="Total number of comments in the topic")

class TopicWithStatsPaginateSchema(PaginationResultSchema[TopicWithStats]):
    pass


class TopicWithStatsAndCharacterNamesPaginateSchema(PaginationResultSchema[TopicWithStatsAndCharacterNames]):
    pass


class CommentBaseRequestSchema(BaseModel):
    text: str = Field(..., description="Text of the comment")
    files_ids: Optional[list[uuid.UUID]] = Field(
        None, description="List of file IDs associated with the comment"
    )


class CommentCreateSchema(CommentBaseRequestSchema):
    pass


class CommentUpdateSchema(CommentBaseRequestSchema):
    pass


class CommentBaseSchema(BaseModel):
    text: str = Field(..., description="Text of the comment")
    topic_id: uuid.UUID = Field(..., description="ID of the topic to which the comment belongs")
    author_user_id: uuid.UUID = Field(..., description="ID of the user who created the comment")


class CommentCreateDBSchema(CommentBaseSchema, CreateBaseModel):
    pass

class CommentUpdateDBSchema(CommentBaseSchema, UpdateBaseModel):
    pass

class CommentReadDBSchema(CommentBaseSchema, TimestampMixin):
    id: uuid.UUID = Field(..., description="Unique identifier of the comment")

    class Config:
        from_attributes = True



class TopicCommentCreateSchema(BaseModel):
    topic: TopicCreateSchema = Field(..., description="Topic to which the comment belongs")
    comment: CommentCreateSchema = Field(None, description="Comment details if applicable")


class FileBaseModel(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier of the file")
    comment_id: uuid.UUID = Field(..., description="ID of the comment to which the file belongs")


class FileCreateSchema(FileBaseModel, CreateBaseModel):
    pass


class FileUpdateSchema(FileBaseModel, UpdateBaseModel):
    pass


class FileReadSchema(FileBaseModel, TimestampMixin):
    
    class Config:
        from_attributes = True


class CommentReadSchema(CommentReadDBSchema):
    files: Optional[list[FileReadSchema]] = Field(
        None, description="List of files associated with the comment"
    )

    class Config:
        from_attributes = True


class CommentReadDBPaginateSchema(PaginationResultSchema[CommentReadSchema]):
    pass


class TopicCommentReadDBSchema(BaseModel):
    topic: TopicReadSchema = Field(..., description="Topic to which the comment belongs")
    comment: CommentReadSchema = Field(None, description="Comment details if applicable")


class CommentReadWithCharacterNameSchema(CommentReadSchema):
    author_character_name: Optional[str] = Field(
        None, description="Name of the character who created the comment"
    )

    files: Optional[list[FileWithUrlReadSchema]] = Field(
        None, description="List of files associated with the comment"
    )

    class Config:
        from_attributes = True

class TopicCommentReadSchema(BaseModel):
    topic: TopicReadWithCharacterNameSchema = Field(..., description="Topic to which the comment belongs")
    comment: CommentReadWithCharacterNameSchema = Field(None, description="Comment details with character name if applicable")

    class Config:
        from_attributes = True


class CommentReadWithCharacterNamePaginateSchema(PaginationResultSchema[CommentReadWithCharacterNameSchema]):
    pass