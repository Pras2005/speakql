from repositories.tenant_repository import TenantRepository
from models.tenant_model import Organization, Workspace, Membership, MembershipRole
from typing import List, Optional

class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo

    async def setup_default_tenant(self, user_id: int):
        # Phase 1 requirement: Create default org/workspace for existing/new users
        org = Organization(name="Default Organization")
        org = await self.tenant_repo.create_org(org)
        
        workspace = Workspace(org_id=org.id, name="Default Workspace")
        workspace = await self.tenant_repo.create_workspace(workspace)
        
        membership = Membership(
            org_id=org.id,
            workspace_id=workspace.id,
            user_id=user_id,
            role=MembershipRole.ADMIN
        )
        await self.tenant_repo.create_membership(membership)
        return org, workspace

    async def get_user_memberships(self, user_id: int) -> List[Membership]:
        return await self.tenant_repo.list_user_memberships(user_id)

    async def get_membership(self, user_id: int, workspace_id: int) -> Optional[Membership]:
        return await self.tenant_repo.get_membership(user_id, workspace_id)
