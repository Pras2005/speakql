from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, JSON

class AuditEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Optional for system-level events (e.g. LOGIN_FAILURE), 
    # but required by service logic for all workspace-owned actions.
    org_id: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspace.id", index=True)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    
    event_type: str = Field(index=True)
    request_id: Optional[str] = Field(default=None, index=True)
    
    # Store dynamic event details in a JSON column
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
