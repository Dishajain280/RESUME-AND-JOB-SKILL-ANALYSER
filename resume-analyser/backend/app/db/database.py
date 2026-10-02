"""
SQLAlchemy database engine & session factory.
Uses SQLite by default (file: resume_analyser.db in the project root).
Set DATABASE_URL in .env to switch to PostgreSQL.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db() -> bool:
    """True when the database accepts a trivial query (used by /health)."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as exc:
        import structlog

        structlog.get_logger().error("db_health_check_failed", error=str(exc))
        return False


def init_db():
    """
    Create all tables if they don't exist (idempotent).

    Intended for development and tests only. Production deployments should
    set AUTO_CREATE_TABLES=false and manage schema with Alembic:

        alembic upgrade head
    """
    if not settings.AUTO_CREATE_TABLES:
        return
    # Import models so Base.metadata knows about them
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
