from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from core.config import settings

# Shared engine and session factory
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,     # Verify connections before use to handle stale pool connections
    pool_recycle=1800,      # Recycle connections every 30 minutes to avoid server-side timeouts
)

# Shared session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # SQLModel doesn't have native async support for metadata.create_all yet,
        # but we can run it in a sync-like fashion through the connection
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
