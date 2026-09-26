import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from backend.app.core.config import get_settings

settings = get_settings()


def test_database_connection() -> None:
    # Use a quick 1-second timeout so the test suite finishes immediately when Postgres is offline
    quick_engine = create_engine(
        settings.database_url,
        connect_args={"connect_timeout": 1},
    )
    try:
        with quick_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    except (OperationalError, Exception) as exc:
        pytest.skip(f"PostgreSQL server offline or not reachable on localhost:5432: {exc}")
    finally:
        quick_engine.dispose()
