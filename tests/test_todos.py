"""
Tests for the AI-Powered Todo API.

Run with:  pytest tests/ -v

Tests use an in-memory SQLite DB — no real PostgreSQL or Anthropic key needed.
Settings are patched before the app is imported so missing env vars don't crash startup.
"""
import pytest
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-not-used")
from fastapi.testclient import TestClient  
from sqlalchemy import create_engine  
from sqlalchemy.orm import sessionmaker  
from app.main import app  
from app.core.database import Base, get_db  
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
@pytest.fixture(autouse=True)
def reset_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

# Helpers
def make_todo(client, **kwargs):
    """Create a todo and return the JSON response."""
    payload = {"title": "Default task", **kwargs}
    resp = client.post("/todos/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()

#  Health
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

# Create
def test_create_todo_minimal(client):
    r = client.post("/todos/", json={"title": "Buy groceries"})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Buy groceries"
    assert data["priority"] == "medium"
    assert data["is_completed"] is False
    assert data["tags"] == []

def test_create_todo_full(client):
    payload = {
        "title": "Review PR",
        "description": "Check the open pull request on GitHub",
        "due_date": "2025-12-31T23:59:00",
        "priority": "high",
        "tags": ["work", "code"],
    }
    r = client.post("/todos/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Review PR"
    assert data["priority"] == "high"
    assert "work" in data["tags"]

def test_create_todo_empty_title_fails(client):
    r = client.post("/todos/", json={"title": ""})
    assert r.status_code == 422

def test_create_todo_whitespace_title_fails(client):
    r = client.post("/todos/", json={"title": "   "})
    assert r.status_code == 422

def test_create_todo_invalid_priority_fails(client):
    r = client.post("/todos/", json={"title": "Task", "priority": "urgent"})
    assert r.status_code == 422

def test_create_todo_missing_title_fails(client):
    r = client.post("/todos/", json={"description": "No title here"})
    assert r.status_code == 422

# Read
def test_get_todo_by_id(client):
    created = make_todo(client, title="Dentist appointment")
    r = client.get(f"/todos/{created['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Dentist appointment"

def test_get_todo_not_found(client):
    r = client.get("/todos/9999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

def test_list_todos_empty(client):
    r = client.get("/todos/")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0

def test_list_todos_returns_created(client):
    make_todo(client, title="Task A")
    make_todo(client, title="Task B")
    r = client.get("/todos/")
    assert r.status_code == 200
    assert r.json()["total"] == 2

def test_list_todos_filter_completed(client):
    make_todo(client, title="Pending task")
    done = make_todo(client, title="Done task")
    client.put(f"/todos/{done['id']}", json={"is_completed": True})
    r = client.get("/todos/?status=completed")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Done task"

def test_list_todos_filter_pending(client):
    make_todo(client, title="Still pending")
    done = make_todo(client, title="Already done")
    client.put(f"/todos/{done['id']}", json={"is_completed": True})
    r = client.get("/todos/?status=pending")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["title"] == "Still pending"

def test_list_todos_filter_priority(client):
    make_todo(client, title="Low thing", priority="low")
    make_todo(client, title="High thing", priority="high")
    r = client.get("/todos/?priority=high")
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["priority"] == "high" for i in items)

def test_list_todos_search(client):
    make_todo(client, title="Buy milk", description="From the grocery store")
    make_todo(client, title="Call dentist")
    r = client.get("/todos/?search=milk")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["title"] == "Buy milk"

def test_list_todos_search_description(client):
    make_todo(client, title="Task", description="Contains the keyword meeting inside")
    make_todo(client, title="Other task")
    r = client.get("/todos/?search=meeting")
    assert r.status_code == 200
    assert r.json()["total"] == 1

def test_list_todos_pagination(client):
    for i in range(5):
        make_todo(client, title=f"Task {i}")
    r = client.get("/todos/?page=1&page_size=2")
    data = r.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

def test_list_todos_sort_by_title_asc(client):
    make_todo(client, title="Zebra task")
    make_todo(client, title="Alpha task")
    r = client.get("/todos/?sort_by=title&sort_order=asc")
    items = r.json()["items"]
    assert items[0]["title"] == "Alpha task"

def test_list_todos_filter_by_tag(client):
    make_todo(client, title="Work task", tags=["work"])
    make_todo(client, title="Personal task", tags=["personal"])
    r = client.get("/todos/?tag=work")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Work task"

# Update
def test_update_todo_partial(client):
    todo = make_todo(client, title="Original title")
    r = client.put(f"/todos/{todo['id']}", json={"is_completed": True})
    assert r.status_code == 200
    data = r.json()
    assert data["is_completed"] is True
    assert data["title"] == "Original title"  

def test_update_todo_full(client):
    todo = make_todo(client, title="Old title")
    r = client.put(f"/todos/{todo['id']}", json={
        "title": "New title",
        "priority": "high",
        "is_completed": True,
        "tags": ["updated"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New title"
    assert data["priority"] == "high"
    assert data["is_completed"] is True

def test_update_todo_not_found(client):
    r = client.put("/todos/9999", json={"title": "Ghost"})
    assert r.status_code == 404

def test_update_todo_empty_title_fails(client):
    todo = make_todo(client, title="Valid title")
    r = client.put(f"/todos/{todo['id']}", json={"title": ""})
    assert r.status_code == 422

# Delete
def test_delete_todo(client):
    todo = make_todo(client, title="To be deleted")
    r = client.delete(f"/todos/{todo['id']}")
    assert r.status_code == 204
    r2 = client.get(f"/todos/{todo['id']}")
    assert r2.status_code == 404

def test_delete_todo_not_found(client):
    r = client.delete("/todos/9999")
    assert r.status_code == 404
