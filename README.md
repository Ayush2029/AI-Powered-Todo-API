# AI-Powered Todo API

A production-grade REST API for todo management built with **FastAPI** and **PostgreSQL**, deployed on **Render**, with AI-powered features using **Groq.**

> Storage is 100% cloud-managed. No local files, no SQLite. The app refuses to start without a valid `DATABASE_URL`, preventing silent data loss on ephemeral containers.

---

## Features

### Core 
- Full CRUD with all required fields (id, title, description, due_date, priority, is_completed, tags, created_at, updated_at)
- Filter by status (`all` / `completed` / `pending`) and priority
- Full-text search across title and description (`?search=meeting`)
- Sorting (`?sort_by=due_date&sort_order=asc`)
- Pagination (`?page=1&page_size=10`)
- Tags per todo (`["work", "personal"]`)
- Correct HTTP status codes (201, 200, 204, 404, 422)
- Pydantic v2 validation — no raw stack traces in responses
- 25+ pytest tests

### AI Upgrades 

| Endpoint | What it does |
|---|---|
| `POST /ai/breakdown` | Break a high-level goal into actionable todos with priorities and tags |
| `POST /ai/suggest-priority` | Analyze a task and suggest the best priority with reasoning |

**Getting a free Groq API key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with GitHub or email (no credit card)
3. Click **API Keys** → **Create API Key**
4. Done — free tier gives 1000+ requests/day

---

## Project Structure

```
todo-api/
├── app/
│   ├── main.py                    # App factory, middleware, routers, lifespan + create_tables
│   ├── core/
│   │   ├── config.py              # Pydantic settings — DATABASE_URL + GROQ_API_KEY required
│   │   ├── database.py            # SQLAlchemy engine, safe enum + table creation
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
│       └── ai_service.py          # Groq SDK calls — breakdown + priority
├── tests/
│   └── test_todos.py              # 25+ tests, SQLite in-memory override
├── alembic/
│   ├── env.py                     # Reads DATABASE_URL from settings
│   └── versions/
│       └── 0001_initial.py        # Creates todos table + priority enum
├── render.yaml                    # Render: web service + postgres
├── requirements.txt
├── .env.example
├── .python-version
├── runtime.txt
└── README.md
```

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL via Docker (see below)
- A free Groq API key from [console.groq.com](https://console.groq.com)

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
# Set GROQ_API_KEY to your free key from console.groq.com
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup — no migration step needed.

API: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

---

## Running Tests

Tests override env vars with SQLite in-memory before any app module loads — no PostgreSQL or Groq key needed.

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

### Steps

1. Push your code to GitHub.
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. Separately create **New** → **PostgreSQL** → Free plan
6. Copy the **Internal Database URL** from the PostgreSQL service
7. In your web service → **Environment** tab → add:
   - `DATABASE_URL` = Internal Database URL from step 6
   - `GROQ_API_KEY` = your free key from console.groq.com
   - `GROQ_MODEL` = `llama-3.3-70b-versatile`
8. Tables are created automatically on first startup — no manual migration needed.

Your API is live at `https://ai-todo-api.onrender.com`.

### Keeping the service alive (free tier workaround)

Render's free tier spins down after 15 minutes of inactivity — the first request after that takes ~30 seconds to wake up. To prevent this, a cron job pings the health endpoint every 10 minutes.

**Setup using [cron-job.org](https://cron-job.org) (free, no account needed):**

1. Go to [cron-job.org](https://cron-job.org) → sign up free
2. Click **Create Cronjob**
3. Set:
   - **URL:** `https://ai-todo-api.onrender.com/health`
   - **Schedule:** Every 10 minutes
4. Click **Save**

The `/health` endpoint returns `{"status": "healthy"}` and keeps the service warm with zero overhead.

---

### Why no SQLite

Render containers are ephemeral — they reset on every deploy. SQLite files on the local filesystem are silently wiped. `DATABASE_URL` has no default in `config.py`, so the app fails loudly at startup if it's missing rather than creating a local file.

---

## Architecture Notes

- **Groq (free tier)** via `groq` SDK. Model: `llama-3.3-70b-versatile`. Uses standard system/user message roles. Markdown fence stripping handles occasional JSON formatting in responses.
- **Auto table creation** — `create_tables()` runs on every startup. Checks `pg_type` before creating the `priority` enum, then calls `Base.metadata.create_all()` which skips existing tables. No Alembic needed at runtime.
- **pool_pre_ping=True** — drops stale DB connections before use, important when app and DB are separate networked services on Render.
- **Error isolation** — `NotFoundError` and `AIServiceError` are global handlers; no tracebacks or SQLAlchemy internals reach clients.
- **Partial updates** — `PUT /todos/{id}` only updates fields present in the request body.

---

## Environment Variables

| Key | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string — injected by Render automatically |
| `GROQ_API_KEY` | Yes | Free key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |

---

## Optional Features Implemented

- [x] Search by title or description
- [x] Sorting by any field
- [x] Pagination
- [x] Tags per todo
- [x] AI task breakdown (`POST /ai/breakdown`)
- [x] AI priority suggestion (`POST /ai/suggest-priority`)
