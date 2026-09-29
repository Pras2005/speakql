from typing import List, Optional, Dict, Any
from models.report_model import Report, ReportRun
from repositories.report_repository import ReportRepository, ReportRunRepository
from services.workflow_service import WorkflowService
from services.audit_service import AuditService
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
        database_id: int,
        schedule_cron: str, 
        delivery_config: Dict[str, Any],
        is_enabled: bool = True
    ) -> Report:
        context = get_request_context()
        report = Report(
            workspace_id=context.workspace_id,
            database_id=database_id,
            name=name,
            saved_query_id=saved_query_id,
            schedule_cron=schedule_cron,
            delivery_config=delivery_config,
            is_enabled=is_enabled
        )
        saved = await self.report_repo.create(report)
        await self.audit_service.record_event(
            event_type="REPORT_CREATED",
            user_id=context.user_id,
            details={"report_id": saved.id, "name": saved.name}
        )
        return saved

    async def update_report(
        self,
        report_id: int,
        update_data: Dict[str, Any]
    ) -> Report:
        context = get_request_context()
        report = await self.report_repo.get_by_id(report_id, context.workspace_id)
        if not report:
            raise ValueError("Report not found or access denied")
        
        for key, value in update_data.items():
            if value is not None:
                setattr(report, key, value)
        
        updated = await self.report_repo.update(report)
        await self.audit_service.record_event(
            event_type="REPORT_UPDATED",
            user_id=context.user_id,
            details={"report_id": updated.id, "name": updated.name}
        )
        return updated

    async def list_reports(self) -> List[Report]:
        context = get_request_context()
        return await self.report_repo.list_by_workspace(context.workspace_id)

    async def run_pending_reports(self, db_repo: Any):
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
                user_db = await db_repo.get_by_id(report.database_id)
                if not user_db:
                    continue
                    
                from utils.agent import DatabaseAgent
                from services.ai_service import AIService
                ai_provider = AIService.get_provider("gemini")
                agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider)
                
                await self.run_report(report.id, report.database_id, agent.tools)
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
        
        # Real-ish delivery logic
        delivery_outcome = await self._deliver_report(report, status)
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
        
        # Update report last_ran_at
        report.last_ran_at = datetime.utcnow()
        await self.report_repo.update(report)
        
        return saved_run

    async def _deliver_report(self, report: Report, status: str) -> Dict[str, Any]:
        outcome = {"delivered": status == "success"}
        config = report.delivery_config
        
        if status != "success":
            return {"delivered": False, "error": "Query execution failed"}

        if config.get("email"):
            # Simulate email delivery
            outcome["email"] = "sent"
            
        if config.get("slack_channel"):
            # Simulate Slack delivery
            # In a real app, this would use a Slack client
            outcome["slack"] = f"posted_to_{config['slack_channel']}"
            
        if config.get("webhook_url"):
            # Simulate webhook delivery
            outcome["webhook"] = "called"
            
        return outcome
