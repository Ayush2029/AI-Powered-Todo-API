from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timezone
import enum
from app.core.database import Base

class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(
        Enum("low", "medium", "high", name="priority", create_type=False),
        default="medium",
        nullable=False,
    )
    is_completed = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
