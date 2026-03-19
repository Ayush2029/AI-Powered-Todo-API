# AI-Powered Todo API

A production-grade REST API for todo management built with **FastAPI** and **PostgreSQL**, deployed on **Render**, with **Google Gemini** AI features — completely free, no credit card needed.

> Storage is 100% cloud-managed. No local files, no SQLite. The app refuses to start without a valid `DATABASE_URL`, preventing silent data loss on ephemeral containers.

---

## Features

### Core (assignment requirements)
- Full CRUD with all required fields (id, title, description, due_date, priority, is_completed, tags, created_at, updated_at)
- Filter by status (`all` / `completed` / `pending`) and priority
- Full-text search across title and description (`?search=meeting`)
- Sorting (`?sort_by=due_date&sort_order=asc`)
- Pagination (`?page=1&page_size=10`)
- Tags per todo (`["work", "personal"]`)
- Correct HTTP status codes (201, 200, 204, 404, 422)
- Pydantic v2 validation — no raw stack traces in responses
- 25+ pytest tests

### AI Upgrades (Google Gemini — FREE tier)

| Endpoint | What it does |
|---|---|
| `POST /ai/breakdown` | Break a high-level goal into actionable todos with priorities and tags |
| `POST /ai/suggest-priority` | Analyze a task and suggest the best priority with reasoning |

**Getting a free Gemini API key:**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with a Google account
3. Click **Get API key** → **Create API key**
4. Done — no credit card, no billing setup

---

## Project Structure

```
todo-api/
├── app/
│   ├── main.py                    # App factory, middleware, routers, lifespan
│   ├── core/
│   │   ├── config.py              # Pydantic settings — DATABASE_URL + GEMINI_API_KEY required
│   │   ├── database.py            # SQLAlchemy engine (PostgreSQL, pool_pre_ping)
│   │   └── errors.py              # Custom exceptions + global handlers (no stack traces)
│   ├── models/
│   │   └── todo.py                # SQLAlchemy ORM model
│   ├── schemas/
│   │   ├── todo.py                # Pydantic request/response schemas
│   │   └── ai.py                  # AI endpoint schemas
│   ├── routes/
│   │   ├── todos.py               # CRUD: POST /todos, GET /todos, GET/PUT/DELETE /todos/{id}
│   │   └── ai.py                  # AI: POST /ai/breakdown, POST /ai/suggest-priority
│   └── services/
│       ├── todo_service.py        # Business logic — all DB queries
│       └── ai_service.py          # Google Gemini SDK calls
├── tests/
│   └── test_todos.py              # 25+ tests, SQLite in-memory override
├── alembic/
│   ├── env.py                     # Reads DATABASE_URL from settings
│   └── versions/
│       └── 0001_initial.py        # Creates todos table + priority enum
├── render.yaml                    # Render Blueprint: web service + postgres + migrations
├── requirements.txt
├── .env.example
└── README.md
```

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL via Docker (see below)
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd todo-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start a local PostgreSQL instance (Docker)

```bash
docker run -d \
  --name todos-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=todos_db \
  -e POSTGRES_USER=todos_user \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

### 3. Configure environment

```bash
cp .env.example .env
# Set GEMINI_API_KEY to your free key from aistudio.google.com
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

API: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

---

## Running Tests

Tests override env vars with SQLite in-memory before any app module loads — no PostgreSQL or Gemini key needed.

```bash
pytest tests/ -v
```

---

## API Reference

### Todos

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/todos/` | 201 | Create a todo |
| `GET` | `/todos/` | 200 | List with filters, search, sort, pagination |
| `GET` | `/todos/{id}` | 200 / 404 | Get a single todo |
| `PUT` | `/todos/{id}` | 200 / 404 | Update (partial or full — all fields optional) |
| `DELETE` | `/todos/{id}` | 204 / 404 | Delete a todo |

#### `GET /todos/` query parameters

| Param | Values | Default |
|-------|--------|---------|
| `status` | `all` / `completed` / `pending` | `all` |
| `priority` | `low` / `medium` / `high` | — |
| `search` | any string | — |
| `sort_by` | `created_at` / `updated_at` / `due_date` / `priority` / `title` | `created_at` |
| `sort_order` | `asc` / `desc` | `desc` |
| `tag` | any string | — |
| `page` | integer ≥ 1 | `1` |
| `page_size` | 1–100 | `20` |

### AI Endpoints

#### `POST /ai/breakdown` — Break a goal into tasks

```json
{
  "goal": "Launch my portfolio website by end of month",
  "max_tasks": 5
}
```

Response:
```json
{
  "goal": "Launch my portfolio website by end of month",
  "tasks": [
    {
      "title": "Design homepage layout",
      "description": "Sketch wireframes and choose a color scheme.",
      "priority": "high",
      "tags": ["design", "portfolio"]
    }
  ]
}
```

#### `POST /ai/suggest-priority` — Get priority recommendation

```json
{
  "title": "Submit tax return",
  "description": "File federal and state taxes online",
  "due_date": "2025-04-15"
}
```

Response:
```json
{
  "suggested_priority": "high",
  "reasoning": "Tax returns have a firm government deadline with financial penalties for missing it."
}
```

---

## Deploying to Render

### One-click via Blueprint

1. Push your code to GitHub.
2. Go to [render.com](https://render.com) → **New** → **Blueprint**.
3. Connect your GitHub repo — Render auto-detects `render.yaml` and creates:
   - A **web service** running FastAPI (2 uvicorn workers)
   - A **free PostgreSQL database** (`todos-db`)
   - `DATABASE_URL` wired automatically from DB → service
4. In the Render dashboard → your web service → **Environment** → add:
   - `GEMINI_API_KEY` = your free key from aistudio.google.com
5. `preDeployCommand: alembic upgrade head` runs automatically — no manual migration step.

Your API is live at `https://ai-todo-api.onrender.com`.

### Why no SQLite

Render containers are ephemeral — they reset on every deploy. SQLite files on the local filesystem are silently wiped. `DATABASE_URL` has no default in `config.py`, so the app fails loudly at startup if it's missing rather than creating a local file.

---

## Architecture Notes

- **Google Gemini (free tier)** via `google-generativeai` SDK. Model: `gemini-2.5-flash-preview-04-17`. System prompt prepended to user message (Gemini's standard pattern). Markdown fence stripping handles Gemini's occasional formatting of JSON responses.
- **pool_pre_ping=True** — drops stale DB connections before use, important when app and DB are separate networked services on Render.
- **preDeployCommand** — Alembic migrations run before the new app version takes traffic.
- **Error isolation** — `NotFoundError` and `AIServiceError` are global handlers; no tracebacks or SQLAlchemy internals reach clients.
- **Partial updates** — `PUT /todos/{id}` only updates fields present in the request body.

---

## Optional Features Implemented

- [x] Search by title or description
- [x] Sorting by any field
- [x] Pagination
- [x] Tags per todo
- [x] AI task breakdown (`POST /ai/breakdown`)
- [x] AI priority suggestion (`POST /ai/suggest-priority`)
