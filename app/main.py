from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import create_tables
from app.routes import todos, ai
from app.core.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="AI-Powered Todo API",
    description=(
        "A clean REST API for todo management with AI superpowers: "
        "task breakdown, smart descriptions, priority suggestions, and productivity insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(todos.router, prefix="/todos", tags=["Todos"])
app.include_router(ai.router, prefix="/ai", tags=["AI Features"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "AI-Powered Todo API is running.",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
