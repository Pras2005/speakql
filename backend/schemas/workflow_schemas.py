from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.workflow_model import SavedQueryStatus, SavedQueryVisibility

class SavedQueryCreate(BaseModel):
    name: str
    sql: str
    prompt: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    visibility: SavedQueryVisibility = SavedQueryVisibility.PRIVATE
    is_template: bool = False

class SavedQueryUpdate(BaseModel):
    name: Optional[str] = None
    sql: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    visibility: Optional[SavedQueryVisibility] = None
    status: Optional[SavedQueryStatus] = None

class SavedQueryResponse(BaseModel):
    id: int
    workspace_id: int
    created_by: int
    name: str
    description: Optional[str] = None
    prompt: Optional[str] = None
    sql: str
    tags: Optional[str] = None
    is_template: bool
    status: SavedQueryStatus
    visibility: SavedQueryVisibility
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QueryCommentCreate(BaseModel):
    body: str

class QueryCommentUpdate(BaseModel):
    body: str

class QueryCommentResponse(BaseModel):
    id: int
    user_id: int
    body: str
    is_edited: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SavedQueryReplayRequest(BaseModel):
    db_id: int
    bypass_approval: bool = False

class SavedQueryRejectRequest(BaseModel):
    reason: str

class SQLDiffResponse(BaseModel):
    added_tables: List[str]
    removed_tables: List[str]
    clause_changes: Dict[str, bool]
    error: Optional[str] = None

class ResultDiffResponse(BaseModel):
    row_count_diff: Optional[int] = None
    executed_at_diff_seconds: Optional[float] = None
    snapshot_drift: Optional[bool] = None
    error: Optional[str] = None

class SaveFromHistoryRequest(BaseModel):
    history_id: int
    name: str
    description: Optional[str] = None
