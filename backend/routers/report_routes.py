from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from typing import List
from auth.auth_guards import require_analyst
from repositories.report_repository import ReportRepository, ReportRunRepository
from repositories.workflow_repository import SavedQueryRepository, QueryCommentRepository
from repositories.database_repository import DatabaseRepository
from repositories.audit_repository import AuditRepository
from services.report_service import ReportService
from services.workflow_service import WorkflowService
from services.governance_service import GovernanceService
from services.database_service import DatabaseService
from services.audit_service import AuditService
from schemas.report_schemas import ReportCreate, ReportUpdate, ReportResponse, ReportRunResponse, RunReportRequest
from utils.agent import DatabaseAgent
from services.ai_service import AIService

router = APIRouter()

async def get_report_service(session: AsyncSession = Depends(get_session)):
    report_repo = ReportRepository(session)
    run_repo = ReportRunRepository(session)
    
    # Workflow service dependencies
    query_repo = SavedQueryRepository(session)
    comment_repo = QueryCommentRepository(session)
    
    # Governance service dependencies
    db_repo = DatabaseRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    
    # This is a bit complex, maybe should use a factory or shared dependency
    # For now, let's keep it direct to avoid breaking other things
    from routers.workflow_routes import get_governance_service
    gov_service = await get_governance_service(session)
    
    workflow_service = WorkflowService(query_repo, comment_repo, gov_service)
    
    return ReportService(report_repo, run_repo, workflow_service, audit_service)

@router.post("", response_model=ReportResponse)
async def create_report(
    request: ReportCreate,
    service: ReportService = Depends(get_report_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.create_report(
        name=request.name,
        saved_query_id=request.saved_query_id,
        schedule_cron=request.schedule_cron,
        delivery_config=request.delivery_config
    )

@router.get("", response_model=List[ReportResponse])
async def list_reports(
    service: ReportService = Depends(get_report_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.list_reports()

@router.post("/{report_id}/run", response_model=ReportRunResponse)
async def run_report_manual(
    report_id: int,
    request: RunReportRequest,
    service: ReportService = Depends(get_report_service),
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(require_analyst)
):
    db_repo = DatabaseRepository(session)
    user_db = await db_repo.get_by_id(request.db_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Database not found")
        
    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider)
    
    return await service.run_report(report_id, request.db_id, agent.tools)

@router.get("/{report_id}/runs", response_model=List[ReportRunResponse])
async def list_report_runs(
    report_id: int,
    service: ReportService = Depends(get_report_service),
    token_data: dict = Depends(require_analyst)
):
    from core.request_context import get_request_context
    context = get_request_context()
    return await service.run_repo.list_by_report(report_id, context.workspace_id)
