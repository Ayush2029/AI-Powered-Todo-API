from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
import math
from app.models.todo import Todo, Priority
from app.schemas.todo import TodoCreate, TodoUpdate
from app.core.errors import NotFoundError

def create_todo(db: Session, payload: TodoCreate) -> Todo:
    todo = Todo(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=Priority(payload.priority.value),
        tags=payload.tags or [],
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

def get_todo(db: Session, todo_id: int) -> Todo:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise NotFoundError("Todo", todo_id)
    return todo

def list_todos(
    db: Session,
    status: Optional[str] = "all",
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = None,
) -> dict:
    query = db.query(Todo)

    if status == "completed":
        query = query.filter(Todo.is_completed == True)  
    elif status == "pending":
        query = query.filter(Todo.is_completed == False) 

    if priority:
        query = query.filter(Todo.priority == Priority(priority))

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Todo.title.ilike(pattern),
                Todo.description.ilike(pattern),
            )
        )

    total = query.count()
    sort_column = getattr(Todo, sort_by, Todo.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    if tag:
        items = [t for t in items if t.tags and tag.lower() in [x.lower() for x in t.tags]]
        total = len(items)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, math.ceil(total / page_size)),
    }
    
def update_todo(db: Session, todo_id: int, payload: TodoUpdate) -> Todo:
    todo = get_todo(db, todo_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "priority" and value is not None:
            value = Priority(value)
        setattr(todo, field, value)
    db.commit()
    db.refresh(todo)
    return todo

def delete_todo(db: Session, todo_id: int) -> None:
    todo = get_todo(db, todo_id)
    db.delete(todo)
    db.commit()
