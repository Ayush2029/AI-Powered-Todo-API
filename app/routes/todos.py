from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from app.services import todo_service
router = APIRouter()

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED, summary="Create a todo")
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item. Title is required and must be non-empty."""
    return todo_service.create_todo(db, payload)

@router.get("/", response_model=TodoListResponse, summary="List todos with filters")
def list_todos(
    status: Optional[str] = Query("all", pattern="^(all|completed|pending)$", description="Filter by completion status"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in title and description"),
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|updated_at|due_date|priority|title)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List todos with optional filters:
    - **status**: all / completed / pending
    - **priority**: low / medium / high
    - **search**: full-text search across title and description
    - **sort_by**: created_at | updated_at | due_date | priority | title
    - **sort_order**: asc | desc
    - **tag**: filter by a specific tag
    - **page / page_size**: pagination controls
    """
    return todo_service.list_todos(
        db,
        status=status,
        priority=priority,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        tag=tag,
    )

@router.get("/{todo_id}", response_model=TodoResponse, summary="Get a todo by ID")
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a single todo by its ID. Returns 404 if not found."""
    return todo_service.get_todo(db, todo_id)

@router.put("/{todo_id}", response_model=TodoResponse, summary="Update a todo (partial or full)")
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    """
    Update an existing todo. All fields are optional — send only what you want to change.
    This means both partial (PATCH-style) and full updates are supported via PUT.
    """
    return todo_service.update_todo(db, todo_id, payload)

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a todo")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo by ID. Returns 204 No Content on success, 404 if not found."""
    todo_service.delete_todo(db, todo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
