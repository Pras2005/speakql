from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from typing import List, Any, Optional
from auth.auth_guards import require_analyst, require_compliance
from repositories.workflow_repository import SavedQueryRepository, QueryCommentRepository
from repositories.database_repository import DatabaseRepository
from repositories.database_grant_repository import DatabaseGrantRepository
from repositories.audit_repository import AuditRepository
from repositories.policy_repository import PolicyRepository
from repositories.approval_repository import ApprovalRepository
from repositories.sensitivity_repository import SensitivityRepository
from services.workflow_service import WorkflowService
from services.governance_service import GovernanceService
from services.database_service import DatabaseService
from services.audit_service import AuditService
from services.grant_service import GrantService
from services.policy_service import PolicyService
from services.risk_service import RiskScoringService
from services.approval_service import ApprovalService
from services.sensitivity_service import SensitivityService
from services.masking_service import MaskingService
from services.confidence_service import ConfidenceService
from services.ai_service import AIService
from utils.agent import DatabaseAgent
from models.tenant_model import DatabaseAccessLevel
from schemas.workflow_schemas import (
    SavedQueryCreate, SavedQueryUpdate, SavedQueryResponse, 
    QueryCommentCreate, QueryCommentUpdate, QueryCommentResponse,
    SavedQueryReplayRequest, SavedQueryRejectRequest, SQLDiffResponse, ResultDiffResponse, SaveFromHistoryRequest
)
from schemas.governance_schemas import GovernedQueryResponse

router = APIRouter()

async def get_database_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    grant_repo = DatabaseGrantRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    grant_service = GrantService(grant_repo, db_repo, audit_service)
    return DatabaseService(db_repo, audit_service, grant_service=grant_service)

async def get_governance_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    grant_repo = DatabaseGrantRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    grant_service = GrantService(grant_repo, db_repo, audit_service)
    db_service = DatabaseService(db_repo, audit_service, grant_service=grant_service)
    
    policy_repo = PolicyRepository(session)
    policy_service = PolicyService(policy_repo)
    
    risk_service = RiskScoringService()
    confidence_service = ConfidenceService()
    
    approval_repo = ApprovalRepository(session)
    approval_service = ApprovalService(approval_repo)
    
    sensitivity_repo = SensitivityRepository(session)
    sensitivity_service = SensitivityService(sensitivity_repo)
    masking_service = MaskingService(sensitivity_service)
    
    return GovernanceService(db_service, policy_service, risk_service, approval_service, masking_service, confidence_service)

async def get_workflow_service(
    session: AsyncSession = Depends(get_session),
    gov_service: GovernanceService = Depends(get_governance_service)
):
    query_repo = SavedQueryRepository(session)
    comment_repo = QueryCommentRepository(session)
    return WorkflowService(query_repo, comment_repo, gov_service)

@router.post("/queries/from-history", response_model=SavedQueryResponse)
async def save_query_from_history(
    request: SaveFromHistoryRequest,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.save_from_history(
        history_id=request.history_id,
        name=request.name,
        description=request.description
    )

@router.post("/queries", response_model=SavedQueryResponse)
async def save_query(
    request: SavedQueryCreate,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.save_query(
        name=request.name,
        sql=request.sql,
        prompt=request.prompt,
        description=request.description,
        tags=request.tags,
        visibility=request.visibility,
        is_template=request.is_template
    )

@router.get("/queries", response_model=List[SavedQueryResponse])
async def list_queries(
    search: Optional[str] = None,
    status: Optional[SavedQueryStatus] = None,
    visibility: Optional[SavedQueryVisibility] = None,
    owner_id: Optional[int] = None,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.list_queries(
        search=search,
        status=status,
        visibility=visibility,
        owner_id=owner_id
    )

@router.get("/queries/{query_id}", response_model=SavedQueryResponse)
async def get_query(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    query = await service.get_query(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return query

@router.patch("/queries/{query_id}", response_model=SavedQueryResponse)
async def update_query(
    query_id: int,
    request: SavedQueryUpdate,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    updated = await service.update_query(query_id, request.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return updated

@router.delete("/queries/{query_id}")
async def delete_query(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    success = await service.delete_query(query_id)
    if not success:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return {"status": "deleted"}

@router.post("/queries/{query_id}/submit", response_model=SavedQueryResponse)
async def submit_query(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.submit_for_review(query_id)

@router.post("/queries/{query_id}/approve", response_model=SavedQueryResponse)
async def approve_query(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_compliance)
):
    user_id = int(token_data['sub'])
    return await service.approve_query(query_id, reviewer_id=user_id)

@router.post("/queries/{query_id}/reject", response_model=SavedQueryResponse)
async def reject_query(
    query_id: int,
    request: SavedQueryRejectRequest,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_compliance)
):
    user_id = int(token_data['sub'])
    return await service.reject_query(query_id, reviewer_id=user_id, reason=request.reason)

@router.post("/queries/{query_id}/archive", response_model=SavedQueryResponse)
async def archive_query(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.archive_query(query_id)

@router.post("/queries/{query_id}/replay", response_model=GovernedQueryResponse)
async def replay_query(
    query_id: int,
    request: SavedQueryReplayRequest,
    service: WorkflowService = Depends(get_workflow_service),
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_analyst)
):
    user_id = int(token_data['sub'])
    workspace_id = token_data.get("workspace_id")
    can_query = await db_service.has_database_access(request.db_id, user_id, DatabaseAccessLevel.QUERY)
    if not can_query:
        raise HTTPException(status_code=403, detail="Database query access required")
    user_db = await db_service.db_repo.get_by_id(request.db_id, workspace_id=workspace_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="Database not found")
        
    from models.tenant_model import MembershipRole
    user_role = token_data.get("role")
    can_bypass = user_role in [MembershipRole.ADMIN.value, MembershipRole.COMPLIANCE_ADMIN.value]
    
    # Only allow bypass if user has the role and requested it
    actual_bypass = request.bypass_approval and can_bypass
    
    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider)
    
    result = await service.replay_query(
        query_id=query_id,
        db_id=request.db_id,
        agent_tools=agent.tools,
        bypass_approval=actual_bypass
    )
    
    if result.get("status") != "success" and result.get("status") != "approval_required":
         raise HTTPException(status_code=400, detail=result.get("error"))
         
    return result

@router.post("/queries/{query_id}/comments", response_model=QueryCommentResponse)
async def add_comment(
    query_id: int,
    request: QueryCommentCreate,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.add_comment(query_id, request.body)

@router.get("/queries/{query_id}/comments", response_model=List[QueryCommentResponse])
async def list_comments(
    query_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.list_comments(query_id)

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    success = await service.delete_comment(comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"status": "deleted"}

@router.patch("/comments/{comment_id}", response_model=QueryCommentResponse)
async def update_comment(
    comment_id: int,
    request: QueryCommentUpdate,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    try:
        updated = await service.update_comment(comment_id, request.body)
        if not updated:
            raise HTTPException(status_code=404, detail="Comment not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/diff", response_model=SQLDiffResponse)
async def compute_sql_diff(
    sql_a: str,
    sql_b: str,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.compute_sql_diff(sql_a, sql_b)

@router.get("/runs/diff", response_model=ResultDiffResponse)
async def compute_result_diff(
    run_a_id: int,
    run_b_id: int,
    service: WorkflowService = Depends(get_workflow_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.compute_result_diff(run_a_id, run_b_id)
