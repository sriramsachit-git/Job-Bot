"""
Pytest configuration for integration tests.

Key goals:
- Make `backend/app` importable as `app` when pytest runs from repo root
- Ensure tests use an isolated SQLite DB by default
- Force pytest-asyncio to load so async fixtures (db_session, client) are handled
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force pytest-asyncio plugin to load (fixes "async fixture with no plugin" on pytest 8+/9)
pytest_plugins = ("pytest_asyncio",)


# Repo root: .../job_search_pipeline
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

# Allow `from app.main import app` to work (app package lives in backend/app)
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Default test DB (can be overridden by env)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test_api.db")

import pytest
import httpx
import warnings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Unclosed SSL socket warnings: background HTTP clients (e.g. pipeline/Google API) may
# leave connections open when tests exit. Harmless for tests; filter to reduce noise.
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*ssl.SSLSocket")

# Import after sys.path is fixed above
from app.main import app  # type: ignore
from app.database import Base  # type: ignore
from app.api.deps import get_database  # type: ignore


TEST_DATABASE_URL = os.environ["DATABASE_URL"]

_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

_SessionLocal = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _override_get_database():
    async with _SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def db_session():
    # Ensure tables exist for every test
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _SessionLocal() as session:
        yield session

    # Cleanup tables between tests
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session):
    # Make the app use our test DB session for all route dependencies
    app.dependency_overrides[get_database] = _override_get_database
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

