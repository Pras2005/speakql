from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.user_model import User
from schemas.agent_schemas import GenerateSQLRequest, GenerateSQLResponse, ExecuteSQLRequest, ExecuteSQLResponse
from crud.db_crud import get_user_databases,add_query_history
from utils.utils import run_with_timeout
from utils.agent import DatabaseAgent  
from auth.auth_bearer import JWTBearer
from database import get_session
from utils.visualizer import get_db_structure_json
import asyncio
router = APIRouter()

@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest, session: Session = Depends(get_session), user: User = Depends(JWTBearer())):
    """Generate SQL based on user's request and the database structure."""
    user_id = int(user['sub'])
    user_databases = get_user_databases(session, user_id)

       
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    

    agent = DatabaseAgent(user_db=user_db,debug=True)
    sql =await run_with_timeout(agent.process_request,request.prompt,timeout_seconds=15)

    
    if not sql:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to generate SQL")
    

    return GenerateSQLResponse(raw_sql=sql, confirmation_required=True, message="Do you want to execute this SQL?")
@router.post("/execute-sql", response_model=ExecuteSQLResponse)
async def execute_sql(request: ExecuteSQLRequest, session: Session = Depends(get_session), user: User = Depends(JWTBearer())):
    """Execute the provided raw SQL query."""
    user_id = int(user['sub'])
    user_databases = get_user_databases(session, user_id)
    
    
    user_db = next((db for db in user_databases if db.id == request.db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")

    agent = DatabaseAgent(user_db=user_db,debug=True)
    
    execution_result = await run_with_timeout(agent.tools.execute_query, request.raw_sql, timeout_seconds=15)

    
    if "error" in execution_result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=execution_result["error"])
    
    add_query_history(session, request.db_id, request.raw_sql, request.raw_sql)
    if not isinstance(execution_result, list):
        execution_result = [execution_result]
    
    return ExecuteSQLResponse(status="success", result=execution_result)



@router.get("/visualize-schema")
async def visualize_schema(db_id: int, session: Session = Depends(get_session), user: User = Depends(JWTBearer())):
    """
    Returns the structure and sample data of all tables in the selected database
    for frontend visualization.
    """
    user_id = int(user['sub'])
    user_databases = get_user_databases(session, user_id)

    user_db = next((db for db in user_databases if db.id == db_id), None)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database not found")
    
    agent = DatabaseAgent(user_db=user_db, debug=True)
    print(get_db_structure_json(agent))
    return get_db_structure_json(agent)
