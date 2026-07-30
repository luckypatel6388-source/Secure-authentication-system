from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create Async Engine for MySQL
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG, #for dev keep it true but during deployment/production change it to false
    pool_pre_ping=True,  # Verifies connection health before executing queries
    pool_size=10,
    max_overflow=20
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Shared Base Class for ORM Models
class Base(DeclarativeBase):
    pass

# FastAPI Dependency for Database Sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

#Asyncgenerator is just type annotation that is used to show this function can use await 