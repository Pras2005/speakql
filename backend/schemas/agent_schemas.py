from pydantic import BaseModel
from typing import Optional, List

class GenerateSQLRequest(BaseModel):
    prompt: str
    db_id: int  # The user database ID to be used for SQL generation
    provider_type: Optional[str] = "gemini"
    model_name: Optional[str] = None

class GenerateSQLResponse(BaseModel):
    raw_sql: str
    confirmation_required: bool  # Flag to indicate if confirmation is needed before execution
    message: Optional[str] = None  # Any message that might accompany the response

class ExecuteSQLRequest(BaseModel):
    raw_sql: str
    db_id: int  # The user database ID to execute the SQL on
    original_prompt: Optional[str] = None
    generated_sql: Optional[str] = None
    sql_rationale: Optional[str] = None

class ExecuteSQLResponse(BaseModel):
    status: str
    result: Optional[List[dict]] = None  # Query result (if applicable)
    error: Optional[str] = None  # If any error occurs during SQL execution
    risk_score: Optional[float] = None
    risk_flags: Optional[List[str]] = None
