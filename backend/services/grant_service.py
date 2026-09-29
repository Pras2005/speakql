from datetime import datetime, timezone
from typing import List, Optional

from core.request_context import get_request_context
from models.tenant_model import DatabaseAccessGrant, DatabaseAccessLevel, MembershipRole
from repositories.database_grant_repository import DatabaseGrantRepository
from repositories.database_repository import DatabaseRepository
from services.audit_service import AuditService


ACCESS_RANK = {
    DatabaseAccessLevel.DISCOVER: 1,
    DatabaseAccessLevel.QUERY: 2,
    DatabaseAccessLevel.EXPORT: 3,
    DatabaseAccessLevel.MANAGE: 4,
}


class GrantService:
    def __init__(
        self,
        grant_repo: DatabaseGrantRepository,
        db_repo: DatabaseRepository,
        audit_service: AuditService,
    ):
        self.grant_repo = grant_repo
        self.db_repo = db_repo
        self.audit_service = audit_service

    async def get_grant(self, database_id: int, target_user_id: int) -> Optional[DatabaseAccessGrant]:
        context = get_request_context()
        return await self.grant_repo.get_grant(context.workspace_id, database_id, target_user_id)

    async def list_grants(self, database_id: int) -> List[DatabaseAccessGrant]:
        context = get_request_context()
        await self._validate_database_scope(database_id, context.workspace_id)
        return await self.grant_repo.list_grants_for_database(context.workspace_id, database_id)

    async def grant_access(
        self, database_id: int, target_user_id: int, access_level: DatabaseAccessLevel
    ) -> DatabaseAccessGrant:
        context = get_request_context()
        await self._validate_database_scope(database_id, context.workspace_id)

        existing = await self.grant_repo.get_grant(context.workspace_id, database_id, target_user_id)
        if existing:
            existing.access_level = access_level
            existing.granted_by = context.user_id
            existing.updated_at = datetime.now(timezone.utc)
            updated = await self.grant_repo.update(existing)
            await self.audit_service.record_event(
                event_type="DATABASE_ACCESS_UPDATED",
                user_id=context.user_id,
                details={
                    "database_id": database_id,
                    "target_user_id": target_user_id,
                    "access_level": access_level.value,
                },
            )
            return updated

        grant = DatabaseAccessGrant(
            workspace_id=context.workspace_id,
            database_id=database_id,
            user_id=target_user_id,
            access_level=access_level,
            granted_by=context.user_id,
        )
        created = await self.grant_repo.create(grant)
        await self.audit_service.record_event(
            event_type="DATABASE_ACCESS_GRANTED",
            user_id=context.user_id,
            details={
                "database_id": database_id,
                "target_user_id": target_user_id,
                "access_level": access_level.value,
            },
        )
        return created

    async def revoke_access(self, database_id: int, target_user_id: int) -> bool:
        context = get_request_context()
        await self._validate_database_scope(database_id, context.workspace_id)

        existing = await self.grant_repo.get_grant(context.workspace_id, database_id, target_user_id)
        if not existing:
            return False

        await self.grant_repo.delete(existing)
        await self.audit_service.record_event(
            event_type="DATABASE_ACCESS_REVOKED",
            user_id=context.user_id,
            details={
                "database_id": database_id,
                "target_user_id": target_user_id,
            },
        )
        return True

    async def has_access(
        self, database_id: int, user_id: int, required_level: DatabaseAccessLevel
    ) -> bool:
        context = get_request_context()

        if context.role == MembershipRole.ADMIN.value:
            return True

        grant = await self.grant_repo.get_grant(context.workspace_id, database_id, user_id)
        if not grant:
            return False

        return ACCESS_RANK[grant.access_level] >= ACCESS_RANK[required_level]

    async def list_database_ids_for_user(self, user_id: int) -> List[int]:
        context = get_request_context()
        if context.role == MembershipRole.ADMIN.value:
            databases = await self.db_repo.list_by_workspace(context.workspace_id)
            return [db.id for db in databases]
        return await self.grant_repo.list_database_ids_for_user(context.workspace_id, user_id)

    async def get_effective_access_level(
        self, database_id: int, user_id: int
    ) -> Optional[DatabaseAccessLevel]:
        context = get_request_context()
        if context.role == MembershipRole.ADMIN.value:
            return DatabaseAccessLevel.MANAGE
        grant = await self.grant_repo.get_grant(context.workspace_id, database_id, user_id)
        return grant.access_level if grant else None

    async def _validate_database_scope(self, database_id: int, workspace_id: int) -> None:
        db = await self.db_repo.get_by_id(database_id, workspace_id=workspace_id)
        if not db:
            raise ValueError("Database not found in active workspace")
