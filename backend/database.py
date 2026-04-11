from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from core.config import settings

# Shared engine and session factory
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.SQL_ECHO
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

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
