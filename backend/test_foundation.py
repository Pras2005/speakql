import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from core.config import settings

# Import all models to ensure SQLModel.metadata is populated and relationships resolve
from models.user_model import User
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from models.tenant_model import Organization, Workspace, Membership
from models.audit_model import AuditEvent

from repositories.user_repository import UserRepository
from repositories.tenant_repository import TenantRepository
from repositories.audit_repository import AuditRepository
from services.auth_service import AuthService
from services.tenant_service import TenantService
from services.audit_service import AuditService
from core.auth import decode_token

import pytest_asyncio

# Use a test-specific database URL (SQLite in memory for smoke test)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(loop_scope="function")
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio(loop_scope="function")
async def test_signup_to_login_flow(session):
    # 1. Setup services
    user_repo = UserRepository(session)
    tenant_repo = TenantRepository(session)
    audit_repo = AuditRepository(session)
    
    audit_service = AuditService(audit_repo)
    auth_service = AuthService(user_repo, tenant_repo, audit_service)
    tenant_service = TenantService(tenant_repo)
    
    # 2. Signup
    username = "test_enterprise_user"
    password = "password123"
    user = await auth_service.register_user(username, password)
    
    # Trigger tenant setup
    org, workspace = await tenant_service.setup_default_tenant(user.id)
    
    # 3. Login with workspace context
    memberships = await tenant_service.get_user_memberships(user.id)
    ws_id = memberships[0].workspace_id
    
    authenticated_user = await auth_service.authenticate_user(
        username, 
        password, 
        workspace_id=ws_id
    )
    assert authenticated_user.id == user.id
    
    # Issue Token
    token = await auth_service.create_user_token(user, workspace_id=ws_id)
    payload = decode_token(token)
    assert payload["workspace_id"] == ws_id
    
    # 4. Verify Audit Trail
    result = await session.execute(select(AuditEvent).where(AuditEvent.user_id == user.id))
    audit_events = result.scalars().all()
    event_types = [e.event_type for e in audit_events]
    assert "LOGIN_SUCCESS" in event_types
    
    print("\n[SMOKE TEST SUCCESS] Positive path verified.")

@pytest.mark.asyncio(loop_scope="function")
async def test_failed_login_audit(session):
    # 1. Setup services
    user_repo = UserRepository(session)
    tenant_repo = TenantRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    auth_service = AuthService(user_repo, tenant_repo, audit_service)
    
    # 2. Attempt login for non-existent user
    username = "ghost_user"
    password = "wrongpassword"
    
    authenticated_user = await auth_service.authenticate_user(username, password)
    
    # VERIFY: Auth failed
    assert authenticated_user is None
    
    # 3. Verify Audit Event exists despite no user/tenant context
    result = await session.execute(select(AuditEvent).where(AuditEvent.event_type == "LOGIN_FAILURE"))
    fail_event = result.scalar_one_or_none()
    
    assert fail_event is not None
    assert fail_event.details["username"] == username
    assert fail_event.user_id is None
    assert fail_event.org_id is None
    assert fail_event.workspace_id is None
    
    print("\n[SMOKE TEST SUCCESS] Negative path (Failed Login Audit) verified.")
