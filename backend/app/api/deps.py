"""
API dependencies.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

async def get_database() -> AsyncSession:
    """Get database session."""
    async for session in get_db():
        yield session
