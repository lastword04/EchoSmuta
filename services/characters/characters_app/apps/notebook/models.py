import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped
from shared.models import TimestampMixin
from ...core.db import Base

class Notebook(Base, TimestampMixin):
    __tablename__ = "notebooks"

    character_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), 
                                                    sa.ForeignKey('characters.id', ondelete='CASCADE'),
                                                          nullable=False, unique=True, index=True
                                                          )
    
    text: Mapped[str] = mapped_column(sa.String(5000), nullable=True)