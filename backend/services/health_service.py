from repositories.database_repository import DatabaseRepository
from services.audit_service import AuditService
from utils.db_connection import validate_database_connection
from utils.encryption import decrypt_password
from typing import Dict, Any, List
from datetime import datetime, timezone

class HealthService:
    def __init__(self, db_repo: DatabaseRepository, audit_service: AuditService):
        self.db_repo = db_repo
        self.audit_service = audit_service

    async def check_database_health(self, db_id: int) -> Dict[str, Any]:
        db = await self.db_repo.get_by_id(db_id)
        if not db:
            return {"status": "not_found"}
        
        status = "healthy"
        error_msg = None
        
        try:
            validate_database_connection(
                host=db.host,
                port=db.port,
                db_user=db.db_user,
                db_password=decrypt_password(db.db_password_encrypted),
                db_name=db.db_name
            )
        except Exception as e:
            status = "unhealthy"
            error_msg = str(e)
        
        # Persist status in database record
        now = datetime.now(timezone.utc)
        db.last_health_status = status
        db.last_health_check_at = now
        db.health_failure_summary = error_msg
        await self.db_repo.update(db)

        # Record audit event
        await self.audit_service.record_event(
            event_type="CONNECTOR_HEALTH_CHECK",
            workspace_id=db.workspace_id,
            org_id=db.org_id,
            details={
                "db_id": db.id,
                "db_name": db.db_name,
                "status": status,
                "error": error_msg
            }
        )

        result = {
            "status": status,
            "last_check": now.isoformat(),
            "db_name": db.db_name
        }
        if error_msg:
            result["error"] = error_msg
            
        return result

    async def list_workspace_health(self, workspace_id: int) -> List[Dict[str, Any]]:
        dbs = await self.db_repo.list_by_workspace(workspace_id)
        results = []
        for db in dbs:
            results.append({
                "id": db.id,
                "db_name": db.db_name,
                "status": db.last_health_status or "unknown",
                "last_check": db.last_health_check_at.isoformat() if db.last_health_check_at else None,
                "error": db.health_failure_summary
            })
        return results
