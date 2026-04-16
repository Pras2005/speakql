from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from repositories.policy_repository import PolicyRepository
from repositories.approval_repository import ApprovalRepository
from repositories.user_repository import UserRepository
from repositories.database_repository import DatabaseRepository
from repositories.sensitivity_repository import SensitivityRepository
from services.policy_service import PolicyService
from services.approval_service import ApprovalService
from services.audit_service import AuditService
from services.health_service import HealthService
from services.sensitivity_service import SensitivityService
from repositories.audit_repository import AuditRepository
from auth.auth_bearer import JWTBearer
from auth.auth_guards import require_admin, require_compliance
from schemas.governance_schemas import (
    PolicyCreate, PolicyResponse, 
    SensitivityRuleCreate, SensitivityRuleResponse,
    ConnectorHealthResponse
)
from models.policy_model import Policy
from models.sensitivity_model import SensitivityRule
from models.approval_model import ApprovalStatus
from typing import List, Optional
from datetime import datetime

router = APIRouter()

async def get_policy_service(session: AsyncSession = Depends(get_session)):
    policy_repo = PolicyRepository(session)
    return PolicyService(policy_repo)

async def get_approval_service(session: AsyncSession = Depends(get_session)):
    approval_repo = ApprovalRepository(session)
    return ApprovalService(approval_repo)

async def get_audit_service(session: AsyncSession = Depends(get_session)):
    audit_repo = AuditRepository(session)
    return AuditService(audit_repo)

async def get_health_service(
    session: AsyncSession = Depends(get_session),
    audit_service: AuditService = Depends(get_audit_service)
):
    db_repo = DatabaseRepository(session)
    return HealthService(db_repo, audit_service)

async def get_sensitivity_service(session: AsyncSession = Depends(get_session)):
    sensitivity_repo = SensitivityRepository(session)
    return SensitivityService(sensitivity_repo)

# --- Policy Management ---

@router.post("/policies", response_model=PolicyResponse)
async def create_policy(
    policy_data: PolicyCreate,
    policy_service: PolicyService = Depends(get_policy_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    policy = Policy(
        workspace_id=workspace_id,
        name=policy_data.name,
        description=policy_data.description,
        priority=policy_data.priority,
        rules_json=policy_data.rules
    )
    return await policy_service.policy_repo.create(policy)

@router.get("/policies", response_model=List[PolicyResponse])
async def list_policies(
    policy_service: PolicyService = Depends(get_policy_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    return await policy_service.get_active_policies(workspace_id)

# --- Sensitivity Management ---

@router.post("/sensitivity-rules", response_model=SensitivityRuleResponse)
async def create_sensitivity_rule(
    rule_data: SensitivityRuleCreate,
    sensitivity_service: SensitivityService = Depends(get_sensitivity_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    rule = SensitivityRule(
        workspace_id=workspace_id,
        table_name=rule_data.table_name,
        column_name=rule_data.column_name,
        label=rule_data.label,
        masking_strategy=rule_data.masking_strategy,
        priority=rule_data.priority,
        restricted_roles=rule_data.restricted_roles
    )
    return await sensitivity_service.sensitivity_repo.create(rule)

@router.get("/sensitivity-rules", response_model=List[SensitivityRuleResponse])
async def list_sensitivity_rules(
    sensitivity_service: SensitivityService = Depends(get_sensitivity_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    return await sensitivity_service.sensitivity_repo.list_by_workspace(workspace_id)

# --- Approval Workflow ---

@router.get("/approvals/pending")
async def list_pending_approvals(
    approval_service: ApprovalService = Depends(get_approval_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    return await approval_service.get_pending_requests(workspace_id)

@router.post("/approvals/{request_id}/approve")
async def approve_request(
    request_id: int,
    approval_service: ApprovalService = Depends(get_approval_service),
    audit_service: AuditService = Depends(get_audit_service),
    token_data: dict = Depends(require_compliance)
):
    user_id = int(token_data["sub"])
    org_id = token_data.get("org_id")
    workspace_id = token_data.get("workspace_id")
    request = await approval_service.approve_request(request_id, workspace_id, user_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    await audit_service.record_event(
        event_type="APPROVAL_GRANTED",
        user_id=user_id,
        org_id=org_id,
        workspace_id=request.workspace_id,
        details={"approval_id": request.id, "sql": request.sql_query}
    )
    return {"status": "approved", "request_id": request.id}

@router.post("/approvals/{request_id}/deny")
async def deny_request(
    request_id: int,
    reason: str,
    approval_service: ApprovalService = Depends(get_approval_service),
    audit_service: AuditService = Depends(get_audit_service),
    token_data: dict = Depends(require_compliance)
):
    user_id = int(token_data["sub"])
    org_id = token_data.get("org_id")
    workspace_id = token_data.get("workspace_id")
    request = await approval_service.deny_request(request_id, workspace_id, user_id, reason)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    await audit_service.record_event(
        event_type="APPROVAL_DENIED",
        user_id=user_id,
        org_id=org_id,
        workspace_id=request.workspace_id,
        details={"approval_id": request.id, "reason": reason}
    )
    return {"status": "denied", "request_id": request.id}

# --- Audit Log Viewer ---

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    governance_only: bool = False,
    category: Optional[str] = None,
    audit_service: AuditService = Depends(get_audit_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    events, total = await audit_service.get_events(
        workspace_id, skip, limit, event_type, user_id, start_date, end_date, governance_only, category
    )
    return {
        "events": events,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/audit-logs/verify")
async def verify_audit_chain(
    audit_service: AuditService = Depends(get_audit_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    is_valid = await audit_service.verify_chain(workspace_id)
    return {
        "workspace_id": workspace_id,
        "is_valid": is_valid,
        "timestamp": datetime.utcnow()
    }

# --- Connector Health ---

@router.get("/connector-health", response_model=List[ConnectorHealthResponse])
async def get_connector_health(
    health_service: HealthService = Depends(get_health_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    return await health_service.list_workspace_health(workspace_id)

@router.post("/connector-health/{db_id}/refresh", response_model=ConnectorHealthResponse)
async def refresh_connector_health(
    db_id: int,
    health_service: HealthService = Depends(get_health_service),
    token_data: dict = Depends(require_compliance)
):
    workspace_id = token_data.get("workspace_id")
    # Verify DB belongs to workspace
    db = await health_service.db_repo.get_by_id(db_id)
    if not db or db.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Database not found")
        
    health = await health_service.check_database_health(db_id)
    health["id"] = db_id
    return health
