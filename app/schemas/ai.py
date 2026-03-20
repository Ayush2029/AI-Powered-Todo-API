from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.todo import Priority

class TaskBreakdownRequest(BaseModel):
    goal: str = Field(..., min_length=5, max_length=1000, description="High-level goal to break into tasks")
    max_tasks: int = Field(default=5, ge=2, le=10, description="Maximum number of tasks to generate")

class GeneratedTask(BaseModel):
    title: str
    description: str
    priority: Priority
    tags: List[str]

class TaskBreakdownResponse(BaseModel):
    goal: str
    tasks: List[GeneratedTask]

class PrioritySuggestRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[str] = Field(None, description="ISO date string, e.g. 2025-06-15")

class PrioritySuggestResponse(BaseModel):
    suggested_priority: Priority
    reasoning: str
