import os
import json
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends
from mcp.server.fastapi import FastApiServer
from mcp.types import Tool, TextContent
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories.database_repository import DatabaseRepository
from repositories.audit_repository import AuditRepository
from repositories.policy_repository import PolicyRepository
from repositories.approval_repository import ApprovalRepository
from repositories.sensitivity_repository import SensitivityRepository
from repositories.api_key_repository import ApiKeyRepository
from services.database_service import DatabaseService
from services.audit_service import AuditService
from services.policy_service import PolicyService
from services.governance_service import GovernanceService
from services.risk_service import RiskScoringService
from services.approval_service import ApprovalService
from services.sensitivity_service import SensitivityService
from services.masking_service import MaskingService
from services.confidence_service import ConfidenceService
from services.ai_service import AIService
from utils.agent import DatabaseAgent
from core.request_context import get_request_context, set_request_context, RequestContext
from middleware.request_context_middleware import RequestIDMiddleware
from models.tenant_model import MembershipRole

app = FastAPI(title="SpeakQL MCP Server")
app.add_middleware(RequestIDMiddleware)
mcp_server = FastApiServer(name="speakql-mcp")

async def get_database_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    return DatabaseService(db_repo, audit_service)

async def get_api_key_repository(session: AsyncSession = Depends(get_session)):
    return ApiKeyRepository(session)

async def get_policy_service(session: AsyncSession = Depends(get_session)):
    policy_repo = PolicyRepository(session)
    return PolicyService(policy_repo)

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

async def get_governance_service(
    db_service: DatabaseService = Depends(get_database_service),
    policy_service: PolicyService = Depends(get_policy_service),
    risk_service: RiskScoringService = Depends(get_risk_service),
    approval_service: ApprovalService = Depends(get_approval_service),
    masking_service: MaskingService = Depends(get_masking_service),
    confidence_service: ConfidenceService = Depends(get_confidence_service)
):
    return GovernanceService(db_service, policy_service, risk_service, approval_service, masking_service, confidence_service)

async def authenticate_mcp(
    request: Request,
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repository),
    db_service: DatabaseService = Depends(get_database_service)
):
    """Authenticates the MCP request and returns workspace context."""
    api_key = request.headers.get("X-SpeakQL-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-SpeakQL-API-Key header or api_key query param")
    
    # 1. Try Workspace Key (Enterprise Mode)
    workspace_key = await api_key_repo.get_by_key(api_key)
    if workspace_key:
        context = get_request_context()
        context.user_id = workspace_key.user_id
        context.org_id = workspace_key.org_id
        context.workspace_id = workspace_key.workspace_id
        context.role = workspace_key.role
        set_request_context(context)
        return {"type": "workspace", "key": workspace_key}
    
    # 2. Try Legacy Database Key
    user_db = await db_service.db_repo.get_by_mcp_key(api_key)
    if user_db:
        context = get_request_context()
        context.user_id = user_db.user_id
        context.org_id = user_db.org_id
        context.workspace_id = user_db.workspace_id
        context.role = MembershipRole.ANALYST
        set_request_context(context)
        return {"type": "legacy", "db": user_db}
        
    raise HTTPException(status_code=401, detail="Invalid API Key")

async def get_db_agent(
    request: Request, 
    auth: dict = Depends(authenticate_mcp),
    db_service: DatabaseService = Depends(get_database_service)
) -> DatabaseAgent:
    user_db = None
    
    if auth["type"] == "workspace":
        workspace_key = auth["key"]
        
        # Try to get db_id from tool arguments in request body
        target_db_id = None
        try:
            body = await request.json()
            target_db_id = body.get("arguments", {}).get("db_id")
        except:
            pass
            
        db_id = target_db_id or workspace_key.default_db_id
        if not db_id:
             # Fallback: first DB in workspace
             databases = await db_service.db_repo.list_by_workspace(workspace_key.workspace_id)
             if not databases:
                  raise HTTPException(status_code=400, detail="No databases configured in workspace")
             db_id = databases[0].id
             
        user_db = await db_service.db_repo.get_by_id(db_id)
        if not user_db or user_db.workspace_id != workspace_key.workspace_id:
             raise HTTPException(status_code=404, detail="Database not found or access denied")
    else:
        user_db = auth["db"]
    
    # Setup agent with default provider
    ai_provider = AIService.get_provider("gemini")
    return DatabaseAgent(user_db=user_db, ai_provider=ai_provider)

@mcp_server.tool()
async def ask_database(
    prompt: str, 
    db_id: Optional[int] = None,
    agent: DatabaseAgent = Depends(get_db_agent),
    gov_service: GovernanceService = Depends(get_governance_service)
) -> List[TextContent]:
    """
    Ask a natural language question about the database with governance enforcement.
    Optional 'db_id' can be provided to select a specific database in the workspace.
    """
    sql_data = await agent.process_request(prompt)
    if not sql_data or "sql" not in sql_data:
        return [TextContent(type="text", text="Failed to generate SQL.")]
    
    sql = sql_data["sql"]
    explanation = sql_data.get("explanation")

    # Use GovernanceService to execute the query
    result = await gov_service.execute_governed_query(
        db_id=agent.tools.user_db.id,
        user_id=agent.tools.user_db.user_id,
        sql=sql,
        original_prompt=prompt,
        agent_tools=agent.tools,
        sql_rationale=explanation
    )
    
    if result.get("status") != "success":
        return [TextContent(type="text", text=f"Query blocked or failed: {result.get('error')}")]
        
    output = {
        "result": result["result"],
        "explanation": explanation,
        "metadata": result.get("explainability")
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

@mcp_server.tool()
async def get_schema(
    db_id: Optional[int] = None,
    agent: DatabaseAgent = Depends(get_db_agent)
) -> List[TextContent]:
    """
    Get the database schema (tables and columns).
    Optional 'db_id' can be provided to select a specific database in the workspace.
    """
    schema = await agent.tools.list_schemas_and_tables()
    return [TextContent(type="text", text=json.dumps(schema, indent=2))]

@mcp_server.tool()
async def list_databases(
    auth: dict = Depends(authenticate_mcp),
    db_service: DatabaseService = Depends(get_database_service)
) -> List[TextContent]:
    """List available databases in the workspace."""
    workspace_id = None
    if auth["type"] == "workspace":
        workspace_id = auth["key"].workspace_id
    else:
        workspace_id = auth["db"].workspace_id
        
    databases = await db_service.db_repo.list_by_workspace(workspace_id)
    db_list = [{"id": db.id, "name": db.db_name, "host": db.host} for db in databases]
    return [TextContent(type="text", text=json.dumps(db_list, indent=2))]

app.mount("/mcp", mcp_server.app)
