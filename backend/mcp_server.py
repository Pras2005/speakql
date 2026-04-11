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
from services.database_service import DatabaseService
from services.audit_service import AuditService
from services.ai_service import AIService
from utils.agent import DatabaseAgent

app = FastAPI(title="SpeakQL MCP Server")
mcp_server = FastApiServer(name="speakql-mcp")

async def get_database_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    return DatabaseService(db_repo, audit_service)

async def get_db_agent(
    request: Request, 
    db_service: DatabaseService = Depends(get_database_service)
) -> DatabaseAgent:
    api_key = request.headers.get("X-SpeakQL-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-SpeakQL-API-Key header or api_key query param")
    
    # Resolve database via MCP Key
    user_db = await db_service.db_repo.get_by_mcp_key(api_key)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Setup agent with default provider
    ai_provider = AIService.get_provider("gemini")
    return DatabaseAgent(user_db=user_db, ai_provider=ai_provider)

@mcp_server.tool()
async def ask_database(prompt: str, agent: DatabaseAgent = Depends(get_db_agent)) -> List[TextContent]:
    """Ask a natural language question about the database."""
    sql = await agent.process_request(prompt)
    if not sql:
        return [TextContent(type="text", text="Failed to generate SQL.")]
    
    result = await agent.tools.execute_query(sql)
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

@mcp_server.tool()
async def get_schema(agent: DatabaseAgent = Depends(get_db_agent)) -> List[TextContent]:
    """Get the database schema (tables and columns)."""
    schema = await agent.tools.list_schemas_and_tables()
    return [TextContent(type="text", text=json.dumps(schema, indent=2))]

app.mount("/mcp", mcp_server.app)
