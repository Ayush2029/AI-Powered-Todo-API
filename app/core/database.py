from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    """Create enum type and all tables safely — idempotent, safe to call multiple times."""
    with engine.connect() as conn:
        # Create priority enum only if it doesn't exist
        exists = conn.execute(text(
            "SELECT 1 FROM pg_type WHERE typname = 'priority'"
        )).fetchone()
        if not exists:
            conn.execute(text(
                "CREATE TYPE priority AS ENUM ('low', 'medium', 'high')"
            ))
        conn.commit()

    # create_all is fully idempotent — skips tables that already exist
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
