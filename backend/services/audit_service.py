from repositories.audit_repository import AuditRepository
from models.audit_model import AuditEvent
from core.request_context import get_request_context
from typing import Optional, Dict, Any
from datetime import datetime

class AuditService:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def record_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        context = get_request_context()
        
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id or context.user_id,
            org_id=org_id or context.org_id,
            workspace_id=workspace_id or context.workspace_id,
            request_id=request_id or context.request_id,
            details=details or {}
        )
        return await self.audit_repo.create(event)

    async def verify_chain(self, workspace_id: int) -> bool:
        return await self.audit_repo.verify_chain(workspace_id)

    async def get_events(
        self,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        governance_only: bool = False,
        category: Optional[str] = None
    ):
        return await self.audit_repo.list_by_workspace(
            workspace_id, skip, limit, event_type, user_id, start_date, end_date, governance_only, category
        )
