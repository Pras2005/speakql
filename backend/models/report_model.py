from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from .tenant_model import Workspace
    from .workflow_model import SavedQuery

class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    database_id: int = Field(foreign_key="userdatabase.id", index=True)
    saved_query_id: int = Field(foreign_key="savedquery.id", index=True)
    
    name: str = Field(index=True)
    schedule_cron: str # e.g. "0 9 * * 1" (Every Monday at 9 AM)
    
    delivery_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON)) # e.g. {"email": ["admin@example.com"], "slack_channel": "#reports"}
    
    is_enabled: bool = Field(default=True)
    last_ran_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    saved_query: "SavedQuery" = Relationship()
    runs: List["ReportRun"] = Relationship(back_populates="report")

class ReportRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="report.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    status: str = Field(index=True) # success, failure
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Audit reference for actual execution
    audit_event_id: Optional[int] = Field(default=None, foreign_key="auditevent.id")
    
    error_message: Optional[str] = None
    delivery_outcome: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    report: Report = Relationship(back_populates="runs")
