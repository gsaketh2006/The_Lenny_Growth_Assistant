from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings
from backend.app.core.logging import logger

db_url = settings.effective_database_url

# Build Async Engine
engine_kwargs = {"echo": False}
if "sqlite" in db_url:
    # SQLite async connection args
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Supabase connection pool configuration
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    # Enable SSL for cloud Supabase endpoints
    if "supabase.co" in db_url or "ssl" in db_url:
        engine_kwargs["connect_args"] = {"ssl": "require"}

async_engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initializes the database schema and extensions."""
    logger.info(f"Initializing database with URL: {db_url.split('@')[-1]}")
    async with async_engine.begin() as conn:
        # If postgres, enable extensions
        if "postgresql" in db_url:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            except Exception as e:
                logger.warning(f"Note on Postgres extensions: {e}")
        
        # Create all tables defined in Base metadata
        await conn.run_sync(Base.metadata.create_all)

        # Ensure user_id column exists on sessions in PostgreSQL/Supabase
        if "postgresql" in db_url:
            try:
                from sqlalchemy import text
                await conn.execute(text("""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='sessions' AND column_name='user_id'
                        ) THEN
                            ALTER TABLE sessions ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
                            CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions(user_id);
                        END IF;
                    END $$;
                """))
            except Exception as e:
                logger.warning(f"Note on sessions user_id migration: {e}")

    logger.info("Database schema initialized successfully on Supabase/PostgreSQL.")

