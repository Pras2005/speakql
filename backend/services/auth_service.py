import logging
from repositories.user_repository import UserRepository
from repositories.tenant_repository import TenantRepository
from services.audit_service import AuditService
from models.user_model import User
from core.auth import hash_password, verify_password, create_access_token
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, tenant_repo: TenantRepository, audit_service: AuditService):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        self.audit_service = audit_service

    async def register_user(self, username: str, password: str) -> User:
        existing = await self.user_repo.get_by_username(username)
        if existing:
            raise ValueError("Username already exists")

        hashed_pw = hash_password(password)
        user = User(username=username, password_hash=hashed_pw)
        return await self.user_repo.create(user)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Public accessor so callers don't reach into user_repo directly."""
        return await self.user_repo.get_by_username(username)

    async def authenticate_user(
        self,
        username: str,
        password: str,
        workspace_id: Optional[int] = None,
        resolve_default_workspace: bool = False,
        tenant_service: Optional["TenantService"] = None,
    ) -> Optional[User]:
        """
        Authenticates a user and logs the attempt to the audit vault.

        Args:
            username: plaintext username
            password: plaintext password
            workspace_id: if known, used for audit context enrichment
            resolve_default_workspace: if True and workspace_id is None, resolve
                the first membership to get an org_id for the audit event
            tenant_service: required when resolve_default_workspace=True
        """
        user = await self.user_repo.get_by_username(username)

        # Resolve org context for richer audit events without double-fetching the user
        org_id = None
        if workspace_id:
            ws = await self.tenant_repo.get_workspace_by_id(workspace_id)
            if ws:
                org_id = ws.org_id
        elif resolve_default_workspace and tenant_service and user:
            memberships = await tenant_service.get_user_memberships(user.id)
            if memberships:
                workspace_id = memberships[0].workspace_id
                ws = await self.tenant_repo.get_workspace_by_id(workspace_id)
                if ws:
                    org_id = ws.org_id

        if not user or not verify_password(password, user.password_hash):
            await self.audit_service.record_event(
                event_type="LOGIN_FAILURE",
                org_id=org_id,
                workspace_id=workspace_id,
                details={"username": username}
            )
            return None

        await self.audit_service.record_event(
            event_type="LOGIN_SUCCESS",
            user_id=user.id,
            org_id=org_id,
            workspace_id=workspace_id,
            details={"username": username}
        )
        return user

    async def create_user_token(self, user: User, workspace_id: Optional[int] = None) -> str:
        """
        Creates a JWT token with full enterprise payload.
        """
        payload: Dict[str, Any] = {
            "sub": str(user.id),
            "token_version": user.token_version,
            "username": user.username,
        }

        # If workspace context is provided, enrich the token
        if workspace_id:
            membership = await self.tenant_repo.get_membership(user.id, workspace_id)
            if membership:
                workspace = await self.tenant_repo.get_workspace_by_id(membership.workspace_id)
                organization = await self.tenant_repo.get_org_by_id(membership.org_id)
                payload.update({
                    "org_id": membership.org_id,
                    "workspace_id": membership.workspace_id,
                    "membership_id": membership.id,
                    "role": membership.role,
                    "workspace_name": workspace.name if workspace else None,
                    "org_name": organization.name if organization else None,
                })

        return create_access_token(payload)
