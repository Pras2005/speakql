from services.governance_service import GovernanceService
from services.export_service import ExportService
from services.audit_service import AuditService
from core.request_context import get_request_context
from typing import Dict, Any, Optional
from models.tenant_model import DatabaseAccessLevel

class GovernedExportService:
    def __init__(
        self, 
        gov_service: GovernanceService, 
        export_service: ExportService,
        audit_service: AuditService
    ):
        self.gov_service = gov_service
        self.export_service = export_service
        self.audit_service = audit_service

    async def export_query_results(
        self,
        db_id: int,
        user_id: int,
        sql: str,
        format: str = "csv",
        original_prompt: Optional[str] = None,
        agent_tools: Any = None
    ) -> Dict[str, Any]:
        """
        Executes a governed query and exports the results in the requested format.
        """
        context = get_request_context()
        
        # 1. Audit Request
        await self.audit_service.record_event(
            event_type="DATA_EXPORT_REQUESTED",
            user_id=user_id,
            details={
                "db_id": db_id,
                "format": format,
                "sql": sql,
                "actor": context.user_id,
                "workspace_id": context.workspace_id
            }
        )

        # 2. Execute governed query (already masked and policy-checked)
        result = await self.gov_service.execute_governed_query(
            db_id=db_id,
            user_id=user_id,
            sql=sql,
            original_prompt=original_prompt,
            agent_tools=agent_tools,
            required_access_level=DatabaseAccessLevel.EXPORT,
        )
        
        if result.get("status") != "success":
            return result
            
        # 3. Format and Audit Completion
        data = result.get("result") or []
        query_id = result.get("query_id")
        row_count = len(data)

        try:
            if format == "csv":
                content = self.export_service.to_csv(data)
                media_type = "text/csv"
            elif format == "xlsx":
                content = self.export_service.to_xlsx(data)
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                error_msg = f"Unsupported format: {format}"
                await self.audit_service.record_event(
                    event_type="DATA_EXPORT_FAILED",
                    user_id=user_id,
                    details={
                        "db_id": db_id,
                        "query_id": query_id,
                        "format": format,
                        "error": error_msg,
                        "actor": context.user_id,
                        "workspace_id": context.workspace_id
                    }
                )
                return {"status": "error", "error": error_msg}

            await self.audit_service.record_event(
                event_type="DATA_EXPORT_COMPLETED",
                user_id=user_id,
                details={
                    "db_id": db_id,
                    "query_id": query_id,
                    "format": format,
                    "row_count": row_count,
                    "actor": context.user_id,
                    "workspace_id": context.workspace_id
                }
            )
            
            return {
                "status": "success",
                "content": content,
                "media_type": media_type,
                "filename": f"export_{db_id}.{format}"
            }
        except Exception as e:
            error_msg = str(e)
            await self.audit_service.record_event(
                event_type="DATA_EXPORT_FAILED",
                user_id=user_id,
                details={
                    "db_id": db_id,
                    "query_id": query_id,
                    "format": format,
                    "error": error_msg,
                    "actor": context.user_id,
                    "workspace_id": context.workspace_id
                }
            )
            return {"status": "error", "error": error_msg}
