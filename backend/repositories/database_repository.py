from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from typing import List, Optional

class DatabaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, db_id: int) -> Optional[UserDatabase]:
        return await self.session.get(UserDatabase, db_id)

    async def list_by_workspace(self, workspace_id: int) -> List[UserDatabase]:
        result = await self.session.execute(
            select(UserDatabase).where(UserDatabase.workspace_id == workspace_id)
        )
        return result.scalars().all()

    async def list_by_user(self, user_id: int) -> List[UserDatabase]:
        # Legacy/Compatibility helper
        result = await self.session.execute(
            select(UserDatabase).where(UserDatabase.user_id == user_id)
        )
        return result.scalars().all()

    async def create(self, db: UserDatabase) -> UserDatabase:
        self.session.add(db)
        await self.session.commit()
        await self.session.refresh(db)
        return db

    async def update(self, db: UserDatabase) -> UserDatabase:
        self.session.add(db)
        await self.session.commit()
        await self.session.refresh(db)
        return db

    async def delete(self, db: UserDatabase):
        await self.session.delete(db)
        await self.session.commit()

    async def get_by_mcp_key(self, mcp_key: str) -> Optional[UserDatabase]:
        result = await self.session.execute(
            select(UserDatabase).where(UserDatabase.mcp_api_key == mcp_key)
        )
        return result.scalar_one_or_none()

    async def add_query_history(self, history: QueryHistory) -> QueryHistory:
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def list_query_history(self, db_id: int) -> List[QueryHistory]:
        result = await self.session.execute(
            select(QueryHistory)
            .where(QueryHistory.user_database_id == db_id)
            .order_by(QueryHistory.executed_at.desc())
        )
        return result.scalars().all()
