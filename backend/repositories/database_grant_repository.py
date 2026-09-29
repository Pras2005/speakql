from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.tenant_model import DatabaseAccessGrant


class DatabaseGrantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_grant(
        self, workspace_id: int, database_id: int, user_id: int
    ) -> Optional[DatabaseAccessGrant]:
        result = await self.session.execute(
            select(DatabaseAccessGrant).where(
                DatabaseAccessGrant.workspace_id == workspace_id,
                DatabaseAccessGrant.database_id == database_id,
                DatabaseAccessGrant.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_grants_for_database(
        self, workspace_id: int, database_id: int
    ) -> List[DatabaseAccessGrant]:
        result = await self.session.execute(
            select(DatabaseAccessGrant).where(
                DatabaseAccessGrant.workspace_id == workspace_id,
                DatabaseAccessGrant.database_id == database_id,
            )
        )
        return list(result.scalars().all())

    async def list_database_ids_for_user(self, workspace_id: int, user_id: int) -> List[int]:
        result = await self.session.execute(
            select(DatabaseAccessGrant.database_id).where(
                DatabaseAccessGrant.workspace_id == workspace_id,
                DatabaseAccessGrant.user_id == user_id,
            )
        )
        return list(result.scalars().all())

    async def create(self, grant: DatabaseAccessGrant) -> DatabaseAccessGrant:
        self.session.add(grant)
        await self.session.commit()
        await self.session.refresh(grant)
        return grant

    async def update(self, grant: DatabaseAccessGrant) -> DatabaseAccessGrant:
        self.session.add(grant)
        await self.session.commit()
        await self.session.refresh(grant)
        return grant

    async def delete(self, grant: DatabaseAccessGrant) -> None:
        await self.session.delete(grant)
        await self.session.commit()
