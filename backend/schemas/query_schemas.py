from typing import Optional
from sqlmodel import SQLModel
from datetime import datetime


class QueryHistoryCreate(SQLModel):
    event_type: str = "execution"
    original_prompt: Optional[str] = None
    generated_sql: Optional[str] = None
    executed_sql: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class QueryHistoryRead(SQLModel):
    id: int
    user_database_id: int
    db_id: Optional[int] = None # Alias for user_database_id to match frontend
    event_type: str
    original_prompt: Optional[str]
    prompt: Optional[str] = None # Alias for original_prompt to match frontend
    generated_sql: Optional[str]
    executed_sql: Optional[str]
    raw_sql: Optional[str] = None # Alias for executed_sql or generated_sql to match frontend
    success: bool
    status: Optional[str] = None # Alias for success (success or error)
    error_message: Optional[str]
    error: Optional[str] = None # Alias for error_message to match frontend
    executed_at: datetime
    timestamp: Optional[datetime] = None # Alias for executed_at to match frontend
