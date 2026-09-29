from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.tenant_model import Organization, Workspace, Membership
from typing import List, Optional

class TenantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_org_by_id(self, org_id: int) -> Optional[Organization]:
        return await self.session.get(Organization, org_id)

    async def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        return await self.session.get(Workspace, workspace_id)

    async def get_membership(self, user_id: int, workspace_id: int) -> Optional[Membership]:
        result = await self.session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.workspace_id == workspace_id
            )
        )
        return result.scalar_one_or_none()

    async def list_user_memberships(self, user_id: int) -> List[Membership]:
        result = await self.session.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        return result.scalars().all()

    async def create_org(self, org: Organization) -> Organization:
        self.session.add(org)
        await self.session.commit()
        await self.session.refresh(org)
        return org

    async def create_workspace(self, workspace: Workspace) -> Workspace:
        self.session.add(workspace)
        await self.session.commit()
        await self.session.refresh(workspace)
        return workspace

    async def create_membership(self, membership: Membership) -> Membership:
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(membership)
        return membership
