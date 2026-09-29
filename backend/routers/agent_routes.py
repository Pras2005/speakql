from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models.user_model import User
from schemas.agent_schemas import GenerateSQLRequest, GenerateSQLResponse, ExecuteSQLRequest, ExecuteSQLResponse
from schemas.governance_schemas import GovernedQueryResponse
from utils.utils import run_with_timeout
from utils.agent import DatabaseAgent  
from auth.auth_bearer import JWTBearer
from auth.auth_guards import require_analyst
from utils.sql_safety import validate_sql_safety
from utils.visualizer import get_db_structure_json
from repositories.database_repository import DatabaseRepository
from repositories.audit_repository import AuditRepository
from repositories.policy_repository import PolicyRepository
from repositories.approval_repository import ApprovalRepository
from repositories.sensitivity_repository import SensitivityRepository
from repositories.catalog_repository import CatalogRepository, BusinessTermRepository, MetricDefinitionRepository
from services.database_service import DatabaseService
from services.audit_service import AuditService
from services.policy_service import PolicyService
from services.governance_service import GovernanceService
from services.risk_service import RiskScoringService
from services.approval_service import ApprovalService
from services.sensitivity_service import SensitivityService
from services.masking_service import MaskingService
from services.confidence_service import ConfidenceService
from services.export_service import ExportService
from services.governed_export_service import GovernedExportService
from services.ai_service import AIService
from services.catalog_service import CatalogService

router = APIRouter()

async def get_policy_service(session: AsyncSession = Depends(get_session)):
    policy_repo = PolicyRepository(session)
    return PolicyService(policy_repo)

async def get_audit_service(session: AsyncSession = Depends(get_session)):
    audit_repo = AuditRepository(session)
    return AuditService(audit_repo)

async def get_risk_service():
    return RiskScoringService()

async def get_confidence_service():
    return ConfidenceService()

async def get_approval_service(session: AsyncSession = Depends(get_session)):
    approval_repo = ApprovalRepository(session)
    return ApprovalService(approval_repo)

async def get_sensitivity_service(session: AsyncSession = Depends(get_session)):
    sensitivity_repo = SensitivityRepository(session)
    return SensitivityService(sensitivity_repo)

async def get_masking_service(sensitivity_service: SensitivityService = Depends(get_sensitivity_service)):
    return MaskingService(sensitivity_service)

async def get_export_service():
    return ExportService()

async def get_database_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    return DatabaseService(db_repo, audit_service)

async def get_catalog_service(session: AsyncSession = Depends(get_session)):
    catalog_repo = CatalogRepository(session)
    glossary_repo = BusinessTermRepository(session)
    metric_repo = MetricDefinitionRepository(session)
    return CatalogService(catalog_repo, glossary_repo, metric_repo)

async def get_governance_service(
    db_service: DatabaseService = Depends(get_database_service),
    policy_service: PolicyService = Depends(get_policy_service),
    risk_service: RiskScoringService = Depends(get_risk_service),
    approval_service: ApprovalService = Depends(get_approval_service),
    masking_service: MaskingService = Depends(get_masking_service),
    confidence_service: ConfidenceService = Depends(get_confidence_service)
):
    return GovernanceService(db_service, policy_service, risk_service, approval_service, masking_service, confidence_service)

async def get_governed_export_service(
    gov_service: GovernanceService = Depends(get_governance_service),
    export_service: ExportService = Depends(get_export_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    return GovernedExportService(gov_service, export_service, audit_service)

@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(
    request: GenerateSQLRequest, 
    db_service: DatabaseService = Depends(get_database_service), 
    catalog_service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_analyst)
):
    """Generate SQL based on user's request and the database structure."""
    user_id = int(token_data['sub'])
    user_databases = await db_service.get_databases(user_id)
       
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    
    # Get semantic context (glossary and metrics)
    semantic_context = await catalog_service.get_semantic_context()
    
    ai_provider = AIService.get_provider(
        request.provider_type or "gemini", 
        request.model_name
    )
    agent = DatabaseAgent(
        user_db=user_db,
        ai_provider=ai_provider,
        debug=True,
        semantic_context=semantic_context
    )
    sql_data = await run_with_timeout(agent.process_request, request.prompt, timeout_seconds=15)
    
    if not sql_data:
        await db_service.log_query(
            db_id=request.db_id,
            user_id=user_id,
            event_type="generation",
            prompt=request.prompt,
            success=False,
            error="Failed to generate SQL"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to generate SQL")

    sql = sql_data["sql"]
    explanation = sql_data.get("explanation")

    await db_service.log_query(
        db_id=request.db_id,
        user_id=user_id,
        event_type="generation",
        prompt=request.prompt,
        generated_sql=sql,
        success=True,
    )

    return GenerateSQLResponse(
        raw_sql=sql, 
        confirmation_required=True, 
        message=explanation or "Do you want to execute this SQL?"
    )

@router.post("/execute-sql", response_model=GovernedQueryResponse)
async def execute_sql(
    request: ExecuteSQLRequest, 
    gov_service: GovernanceService = Depends(get_governance_service), 
    token_data: dict = Depends(require_analyst)
):
    """Execute the provided raw SQL query with governance enforcement."""
    user_id = int(token_data['sub'])
    user_databases = await gov_service.db_service.get_databases(user_id)
    
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")

    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider, debug=True)
    
    result = await gov_service.execute_governed_query(
        db_id=request.db_id,
        user_id=user_id,
        sql=request.raw_sql,
        original_prompt=request.original_prompt,
        agent_tools=agent.tools,
        sql_rationale=request.sql_rationale
    )

    if result.get("status") == "approval_required":
        return GovernedQueryResponse(
            status="pending_approval", 
            error=result.get("error"),
            explainability=result["explainability"]
        )

    if result.get("status") != "success":
        error_code = 400
        if result.get("status") == "denied":
            error_code = 403
        
        if "explainability" in result:
             return GovernedQueryResponse(
                 status=result["status"],
                 error=result.get("error"),
                 explainability=result["explainability"]
             )
        
        raise HTTPException(status_code=error_code, detail=result.get("error"))

    execution_result = result["result"]
    if not isinstance(execution_result, list):
        execution_result = [execution_result]
    
    return GovernedQueryResponse(
        status="success", 
        result=execution_result,
        explainability=result["explainability"]
    )

@router.post("/export-sql")
async def export_sql(
    request: ExecuteSQLRequest,
    format: str = "csv",
    export_service: GovernedExportService = Depends(get_governed_export_service),
    token_data: dict = Depends(require_analyst)
):
    """Execute and export SQL query results through governance pipeline."""
    user_id = int(token_data['sub'])
    user_databases = await export_service.gov_service.db_service.get_databases(user_id)
    
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=404, detail="Database not found")

    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider, debug=True)
    
    result = await export_service.export_query_results(
        db_id=request.db_id,
        user_id=user_id,
        sql=request.raw_sql,
        format=format,
        original_prompt=request.original_prompt,
        agent_tools=agent.tools
    )

    if result.get("status") != "success":
        error_code = 400
        if result.get("status") == "denied":
            error_code = 403
        raise HTTPException(status_code=error_code, detail=result.get("error"))

    return Response(
        content=result["content"],
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/visualize-schema")
async def visualize_schema(
    db_id: int, 
    db_service: DatabaseService = Depends(get_database_service), 
    token_data: dict = Depends(require_analyst)
):
    """Returns the structure and sample data of all tables in the selected database."""
    user_id = int(token_data['sub'])
    user_databases = await db_service.get_databases(user_id)

    user_db = next((db for db in user_databases if db.id == db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    
    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider, debug=True)
    return await get_db_structure_json(agent)

@router.post("/explain-sql")
async def explain_sql(
    request: ExecuteSQLRequest, 
    gov_service: GovernanceService = Depends(get_governance_service), 
    token_data: dict = Depends(require_analyst)
):
    """Execute EXPLAIN on the provided raw SQL query with governance enforcement."""
    user_id = int(token_data['sub'])
    user_databases = await gov_service.db_service.get_databases(user_id)

    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")

    ai_provider = AIService.get_provider("gemini")
    agent = DatabaseAgent(user_db=user_db, ai_provider=ai_provider, debug=True)
    explain_sql = f"EXPLAIN {request.raw_sql}"
    
    result = await gov_service.execute_governed_query(
        db_id=request.db_id,
        user_id=user_id,
        sql=explain_sql,
        original_prompt=request.original_prompt,
        agent_tools=agent.tools,
        sql_rationale=request.sql_rationale
    )

    if result.get("status") != "success":
        error_code = 400
        if result.get("status") == "denied":
            error_code = 403
        raise HTTPException(status_code=error_code, detail=result.get("error"))

    return {
        "status": "success", 
        "result": result["result"],
        "explainability": result["explainability"]
    }
