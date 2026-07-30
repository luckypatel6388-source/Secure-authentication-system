import logging
from app.db.session import Base,engine

logger = logging.getLogger("app.database")

async def init_db() -> None:
    """Initializes database tables during app startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {str(e)}")
        raise

async def close_db() -> None:
    """Closes database engine connections gracefully on app shutdown."""
    await engine.dispose()
    logger.info("Database connection pool closed.")