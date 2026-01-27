"""
Database setup with SQLAlchemy.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# Create async engine with proper SQLite threading configuration
# For aiosqlite, we need to disable thread checking and use NullPool
# to avoid thread-safety issues with async operations
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,  # Use NullPool to avoid connection sharing issues
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
