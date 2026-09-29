import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.mcp_model import WorkspaceApiKey
from typing import Optional
from datetime import datetime, timezone

class ApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def get_by_key(self, api_key: str) -> Optional[WorkspaceApiKey]:
        hashed = self._hash_key(api_key)
        result = await self.session.execute(
            select(WorkspaceApiKey).where(
                WorkspaceApiKey.hashed_key == hashed,
                WorkspaceApiKey.is_active == True
            )
        )
        key = result.scalar_one_or_none()
        if key:
             key.last_used_at = datetime.now(timezone.utc)
             await self.session.commit()
             await self.session.refresh(key)
        return key

    async def create(self, key: WorkspaceApiKey) -> WorkspaceApiKey:
        self.session.add(key)
        await self.session.commit()
        await self.session.refresh(key)
        return key
