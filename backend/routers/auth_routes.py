from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from repositories.user_repository import UserRepository
from repositories.tenant_repository import TenantRepository
from repositories.audit_repository import AuditRepository
from services.auth_service import AuthService
from services.tenant_service import TenantService
from services.audit_service import AuditService
from schemas.user_schemas import UserCreate, UserRead, UserLogin
from auth.auth_bearer import JWTBearer
from typing import Optional

router = APIRouter()

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

async def get_tenant_service(session: AsyncSession = Depends(get_session)):
    tenant_repo = TenantRepository(session)
    return TenantService(tenant_repo)

@router.post("/signup", response_model=UserRead)
async def signup(
    user_data: UserCreate, 
    auth_service: AuthService = Depends(get_auth_service),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    try:
        user = await auth_service.register_user(user_data.username, user_data.password)
        # Phase 1: Setup default tenant for new users
        await tenant_service.setup_default_tenant(user.id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    credentials: UserLogin, 
    workspace_id: Optional[int] = None,
    auth_service: AuthService = Depends(get_auth_service),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    # If no workspace provided, we try to resolve the first one later, 
    # but authenticate_user needs it for audit if possible.
    if not workspace_id:
        # Pre-resolve default workspace for audit purposes
        # This requires finding the user first
        user_repo = auth_service.user_repo
        user = await user_repo.get_by_username(credentials.username)
        if user:
            memberships = await tenant_service.get_user_memberships(user.id)
            if memberships:
                workspace_id = memberships[0].workspace_id

    user = await auth_service.authenticate_user(
        credentials.username, 
        credentials.password,
        workspace_id=workspace_id
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = await auth_service.create_user_token(user, workspace_id=workspace_id)
    return {"access_token": token}

@router.get("/me")
async def read_current_user(
    token_data: dict = Depends(JWTBearer()), 
    session: AsyncSession = Depends(get_session)
):
    user_id = int(token_data["sub"])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": token_data.get("username", user.username), 
        "user_id": user.id,
        "org_id": token_data.get("org_id"),
        "org_name": token_data.get("org_name"),
        "workspace_id": token_data.get("workspace_id"),
        "workspace_name": token_data.get("workspace_name"),
        "role": token_data.get("role")
    }
