from typing import List, Optional, Dict, Any
from models.report_model import Report, ReportRun
from repositories.report_repository import ReportRepository, ReportRunRepository
from services.workflow_service import WorkflowService
from core.request_context import get_request_context, RequestContext, set_request_context
from datetime import datetime

class ReportService:
    def __init__(
        self, 
        report_repo: ReportRepository, 
        run_repo: ReportRunRepository,
        workflow_service: WorkflowService,
        audit_service: AuditService
    ):
        self.report_repo = report_repo
        self.run_repo = run_repo
        self.workflow_service = workflow_service
        self.audit_service = audit_service

    async def create_report(
        self, 
        name: str, 
        saved_query_id: int, 
        schedule_cron: str, 
        delivery_config: Dict[str, Any]
    ) -> Report:
        context = get_request_context()
        report = Report(
            workspace_id=context.workspace_id,
            name=name,
            saved_query_id=saved_query_id,
            schedule_cron=schedule_cron,
            delivery_config=delivery_config
        )
        saved = await self.report_repo.create(report)
        await self.audit_service.record_event(
            event_type="REPORT_CREATED",
            user_id=context.user_id,
            details={"report_id": saved.id, "name": saved.name}
        )
        return saved

    async def list_reports(self) -> List[Report]:
        context = get_request_context()
        return await self.report_repo.list_by_workspace(context.workspace_id)

    async def run_pending_reports(self, db_id: int, agent_tools: Any):
        """Finds and runs all enabled reports that are due for execution."""
        # This would normally be filtered by cron logic
        # For this implementation, we run all enabled reports that haven't ran in the last hour
        from sqlalchemy import select
        from models.report_model import Report
        
        query = select(Report).where(Report.is_enabled == True)
        result = await self.report_repo.session.execute(query)
        reports = result.scalars().all()
        
        for report in reports:
            # Simple threshold: 1 hour
            if report.last_ran_at:
                delta = datetime.utcnow() - report.last_ran_at
                if delta.total_seconds() < 3600:
                    continue
            
            # Setup context for the report's workspace
            ctx = RequestContext(
                workspace_id=report.workspace_id,
                user_id=0, # System user
                role="admin"
            )
            set_request_context(ctx)
            
            try:
                await self.run_report(report.id, db_id, agent_tools)
            except Exception as e:
                print(f"Failed to run scheduled report {report.id}: {e}")

    async def run_report(self, report_id: int, db_id: int, agent_tools: Any) -> ReportRun:
        context = get_request_context()
        report = await self.report_repo.get_by_id(report_id, context.workspace_id)
        if not report:
            raise ValueError("Report not found or access denied")
            
        # Check if source query is approved
        from models.workflow_model import SavedQueryStatus
        query = await self.workflow_service.get_query(report.saved_query_id)
        if not query:
            raise ValueError("Source query not found")
            
        # Only bypass approval if the query is already approved by compliance
        should_bypass = (query.status == SavedQueryStatus.APPROVED)
        
        # Replay the query through governed path
        result = await self.workflow_service.replay_query(
            query_id=report.saved_query_id,
            db_id=db_id,
            agent_tools=agent_tools,
            bypass_approval=should_bypass
        )
        
        status = "success" if result.get("status") == "success" else "failure"
        error_msg = result.get("error") if status == "failure" else None
        
        run = ReportRun(
            report_id=report.id,
            workspace_id=report.workspace_id,
            status=status,
            error_message=error_msg,
            audit_event_id=result.get("query_id") # Reusing query_id as audit ref
        )
        
        # Simulate delivery
        delivery_outcome = {"delivered": status == "success"}
        if report.delivery_config.get("email"):
            delivery_outcome["email"] = "sent" if status == "success" else "failed"
            
        run.delivery_outcome = delivery_outcome
        
        saved_run = await self.run_repo.create(run)
        
        # Log delivery outcome to audit service
        await self.audit_service.record_event(
            event_type="REPORT_RUN_COMPLETED",
            user_id=context.user_id,
            details={
                "report_id": report.id,
                "run_id": saved_run.id,
                "status": status,
                "delivery_outcome": delivery_outcome
            }
        )
        
        report.last_ran_at = datetime.utcnow()
        await self.report_repo.update(report)
        
        return saved_run
