from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title (required, non-empty)")
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = None
    priority: Priority = Priority.medium
    tags: Optional[List[str]] = Field(default_factory=list)
    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be blank or whitespace only.")
        return v.strip()
    @field_validator("tags")
    @classmethod
    def tags_lowercase(cls, v):
        if v is None:
            return []
        return [tag.lower().strip() for tag in v if tag.strip()]

class TodoUpdate(BaseModel):
    """Supports partial updates — all fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = None
    priority: Optional[Priority] = None
    is_completed: Optional[bool] = None
    tags: Optional[List[str]] = None
    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title must not be blank or whitespace only.")
        return v.strip() if v else v
    @field_validator("tags")
    @classmethod
    def tags_lowercase(cls, v):
        if v is None:
            return None
        return [tag.lower().strip() for tag in v if tag.strip()]

class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: Priority
    is_completed: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TodoListResponse(BaseModel):
    items: List[TodoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
