import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings

logger = logging.getLogger("gys_crm.db")
settings = get_settings()

connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"connect_timeout": 2}

try:
    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except (OperationalError, Exception) as exc:
    logger.warning(
        f"PostgreSQL database not available ({exc}). Falling back to SQLite local database (gys_crm.db)."
    )
    engine = create_engine(
        "sqlite:///./gys_crm.db",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
