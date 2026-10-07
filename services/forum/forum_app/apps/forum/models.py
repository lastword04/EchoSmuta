from sqlalchemy import UUID, String, Text, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import uuid
from shared.models import TimestampMixin
from .enums import ForumSection
from ...core.db import Base

class Forum(Base, TimestampMixin):
    __tablename__ = 'forums'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    section: Mapped[ForumSection] = mapped_column(Enum(ForumSection), nullable=False)
    last_comment_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_comment_datetime: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Отношения
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="forum", cascade="all, delete-orphan")

class Topic(Base, TimestampMixin):
    __tablename__ = 'topics'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forum_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('forums.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_comment_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_comment_datetime: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Отношения
    forum: Mapped["Forum"] = relationship("Forum", back_populates="topics")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="topic", cascade="all, delete-orphan")

class Comment(Base, TimestampMixin):
    __tablename__ = 'comments'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('topics.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Отношения
    topic: Mapped["Topic"] = relationship("Topic", back_populates="comments")

    files: Mapped[list["File"]] = relationship("File", back_populates="comment", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = 'files'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('comments.id'), nullable=False)

    comment: Mapped["Comment"] = relationship("Comment", back_populates="files")