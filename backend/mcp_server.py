import os
import json
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends
from mcp.server.fastapi import FastApiServer
from mcp.types import Tool, TextContent
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from crud.db_crud import get_user_database_by_mcp_key
from utils.agent import DatabaseAgent

app = FastAPI(title="SpeakQL MCP Server")
mcp_server = FastApiServer(name="speakql-mcp")

async def get_db_agent(request: Request, session: AsyncSession = Depends(get_session)) -> DatabaseAgent:
    # MCP SSE sends headers. We check for our custom API Key.
    api_key = request.headers.get("X-SpeakQL-API-Key")
    if not api_key:
        # Some MCP clients might use query params if headers are restricted
        api_key = request.query_params.get("api_key")
        
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-SpeakQL-API-Key header or api_key query param")
    
    user_db = await get_user_database_by_mcp_key(session, api_key)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return DatabaseAgent(user_db=user_db)

@mcp_server.tool()
async def ask_database(prompt: str, agent: DatabaseAgent = Depends(get_db_agent)) -> List[TextContent]:
    """
    Ask a natural language question about the database. 
    The agent will generate and execute SQL to provide an answer.
    """
    sql = await agent.process_request(prompt)
    if not sql:
        return [TextContent(type="text", text="Failed to generate SQL.")]
    
    # Execute the query
    result = await agent.tools.execute_query(sql)
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

@mcp_server.tool()
async def get_schema(agent: DatabaseAgent = Depends(get_db_agent)) -> List[TextContent]:
    """Get the database schema (tables and columns)."""
    schema = await agent.tools.list_schemas_and_tables()
    return [TextContent(type="text", text=json.dumps(schema, indent=2))]

# Mount MCP server on the FastAPI app
# This allows the MCP server to share the same lifecycle and DB sessions
app.mount("/mcp", mcp_server.app)

# Note: In a real deployment, you would run this with:
# uvicorn mcp_server:app --host 0.0.0.0 --port 8001
