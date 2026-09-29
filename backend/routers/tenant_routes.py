from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from repositories.audit_repository import AuditRepository
from services.tenant_service import TenantService
from services.auth_service import AuthService
from services.audit_service import AuditService
from auth.auth_bearer import JWTBearer

router = APIRouter()

async def get_tenant_service(session: AsyncSession = Depends(get_session)):
    tenant_repo = TenantRepository(session)
    return TenantService(tenant_repo)

async def get_audit_service(session: AsyncSession = Depends(get_session)):
    audit_repo = AuditRepository(session)
    return AuditService(audit_repo)

async def get_auth_service(
    session: AsyncSession = Depends(get_session),
    audit_service: AuditService = Depends(get_audit_service)
):
    user_repo = UserRepository(session)
    tenant_repo = TenantRepository(session)
    return AuthService(user_repo, tenant_repo, audit_service)

@router.get("/memberships")
async def list_my_memberships(
    tenant_service: TenantService = Depends(get_tenant_service),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    memberships = await tenant_service.get_user_memberships(user_id)
    return [
        {
            "org_id": m.org_id,
            "workspace_id": m.workspace_id,
            "role": m.role,
            "id": m.id
        }
        for m in memberships
    ]

@router.post("/switch-workspace/{workspace_id}")
async def switch_workspace(
    workspace_id: int,
    tenant_service: TenantService = Depends(get_tenant_service),
    auth_service: AuthService = Depends(get_auth_service),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    
    # Verify membership
    membership = await tenant_service.get_membership(user_id, workspace_id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    
    # Re-issue token with new workspace context
    user_repo = UserRepository(auth_service.user_repo.session)
    user = await user_repo.get_by_id(user_id)
    
    new_token = await auth_service.create_user_token(user, workspace_id=workspace_id)
    
    # Log the switch event
    await auth_service.audit_service.record_event(
        event_type="WORKSPACE_SWITCHED",
        user_id=user_id,
        org_id=membership.org_id,
        workspace_id=workspace_id
    )
    
    return {"access_token": new_token}
