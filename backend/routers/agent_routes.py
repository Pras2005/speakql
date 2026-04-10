from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user_model import User
from schemas.agent_schemas import GenerateSQLRequest, GenerateSQLResponse, ExecuteSQLRequest, ExecuteSQLResponse
from crud.db_crud import get_user_databases,add_query_history
from utils.utils import run_with_timeout
from utils.agent import DatabaseAgent  
from auth.auth_bearer import JWTBearer
from database import get_session
from utils.sql_safety import validate_sql_safety
from utils.visualizer import get_db_structure_json
router = APIRouter()

@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest, session: AsyncSession = Depends(get_session), user: User = Depends(JWTBearer())):
    """Generate SQL based on user's request and the database structure."""
    user_id = int(user['sub'])
    user_databases = await get_user_databases(session, user_id)

       
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    

    agent = DatabaseAgent(
        user_db=user_db,
        provider_type=request.provider_type or "gemini",
        model_name=request.model_name,
        debug=True
    )
    sql =await run_with_timeout(agent.process_request,request.prompt,timeout_seconds=15)

    
    if not sql:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to generate SQL")
    await add_query_history(
        session,
        request.db_id,
        event_type="generation",
        prompt=request.prompt,
        generated_sql=sql,
        success=True,
    )

    return GenerateSQLResponse(raw_sql=sql, confirmation_required=True, message="Do you want to execute this SQL?")
@router.post("/execute-sql", response_model=ExecuteSQLResponse)
async def execute_sql(request: ExecuteSQLRequest, session: AsyncSession = Depends(get_session), user: User = Depends(JWTBearer())):
    """Execute the provided raw SQL query."""
    user_id = int(user['sub'])
    user_databases = await get_user_databases(session, user_id)
    
    
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")

    safety_error = validate_sql_safety(request.raw_sql)
    if safety_error:
        await add_query_history(
            session,
            request.db_id,
            event_type="execution",
            prompt=request.original_prompt or "Execute SQL",
            generated_sql=request.generated_sql or request.raw_sql,
            executed_sql=request.raw_sql,
            success=False,
            error=safety_error,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=safety_error)

    agent = DatabaseAgent(user_db=user_db,debug=True)
    
    execution_result = await run_with_timeout(agent.tools.execute_query, request.raw_sql, timeout_seconds=15)

    if execution_result is None:
        await add_query_history(
            session,
            request.db_id,
            event_type="execution",
            prompt=request.original_prompt or "Execute SQL",
            generated_sql=request.generated_sql or request.raw_sql,
            executed_sql=request.raw_sql,
            success=False,
            error="SQL execution timed out",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQL execution timed out")

    if "error" in execution_result:
        await add_query_history(
            session,
            request.db_id,
            event_type="execution",
            prompt=request.original_prompt or "Execute SQL",
            generated_sql=request.generated_sql or request.raw_sql,
            executed_sql=request.raw_sql,
            success=False,
            error=execution_result["error"],
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=execution_result["error"])
    
    await add_query_history(
        session,
        request.db_id,
        event_type="execution",
        prompt=request.original_prompt or "Execute SQL",
        generated_sql=request.generated_sql or request.raw_sql,
        executed_sql=request.raw_sql,
        success=True,
    )
    if not isinstance(execution_result, list):
        execution_result = [execution_result]
    
    return ExecuteSQLResponse(status="success", result=execution_result)



@router.get("/visualize-schema")
async def visualize_schema(db_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(JWTBearer())):
    """
    Returns the structure and sample data of all tables in the selected database
    for frontend visualization.
    """
    user_id = int(user['sub'])
    user_databases = await get_user_databases(session, user_id)

    user_db = next((db for db in user_databases if db.id == db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    
    agent = DatabaseAgent(user_db=user_db, debug=True)
    return await get_db_structure_json(agent)

@router.post("/explain-sql")
async def explain_sql(request: ExecuteSQLRequest, session: AsyncSession = Depends(get_session), user: User = Depends(JWTBearer())):
    """Execute EXPLAIN on the provided raw SQL query."""
    user_id = int(user['sub'])
    user_databases = await get_user_databases(session, user_id)

    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")

    # Safety check (EXPLAIN is generally safe as it doesn't execute the query, but we still validate)
    safety_error = validate_sql_safety(request.raw_sql)
    if safety_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=safety_error)

    agent = DatabaseAgent(user_db=user_db, debug=True)

    explain_sql = f"EXPLAIN {request.raw_sql}"
    explain_result = await run_with_timeout(agent.tools.execute_query, explain_sql, timeout_seconds=10)

    if explain_result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EXPLAIN timed out")

    if "error" in explain_result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=explain_result["error"])

    return {"status": "success", "result": explain_result}
