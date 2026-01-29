"""
Pytest configuration for integration tests.

Key goals:
- Make `backend/app` importable as `app` when pytest runs from repo root
- Ensure tests use an isolated SQLite DB by default
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

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

