from repositories.audit_repository import AuditRepository
from models.audit_model import AuditEvent
from core.request_context import get_request_context
from typing import Optional, Dict, Any

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
