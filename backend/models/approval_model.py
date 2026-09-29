from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"

class ApprovalRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    requester_id: int = Field(foreign_key="user.id", index=True)
    approver_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    
    # Context of the request
    db_id: int = Field(foreign_key="userdatabase.id")
    sql_query: str
    original_prompt: Optional[str] = None
    
    # Meta
    risk_score: Optional[float] = None
    denial_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
