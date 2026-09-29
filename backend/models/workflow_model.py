from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from .user_model import User
    from .tenant_model import Workspace

class SavedQueryStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class SavedQueryVisibility(str, Enum):
    PRIVATE = "private"
    WORKSPACE_SHARED = "workspace_shared"

class SavedQuery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    created_by: int = Field(foreign_key="user.id", index=True)
    
    name: str = Field(index=True)
    description: Optional[str] = None
    prompt: Optional[str] = None
    sql: str
    tags: Optional[str] = None  # Comma-separated tags or JSON
    
    is_template: bool = Field(default=False)
    status: SavedQueryStatus = Field(default=SavedQueryStatus.DRAFT)
    visibility: SavedQueryVisibility = Field(default=SavedQueryVisibility.PRIVATE)
    
    # Review metadata
    reviewed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    runs: List["SavedQueryRun"] = Relationship(back_populates="saved_query")
    comments: List["QueryComment"] = Relationship(back_populates="saved_query")

class SavedQueryRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    saved_query_id: int = Field(foreign_key="savedquery.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    run_by: int = Field(foreign_key="user.id", index=True)
    
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    row_count: Optional[int] = None
    
    # For snapshot comparison (reference to actual data or digest)
    result_snapshot_ref: Optional[str] = None
    
    # Store meaningful clause metadata for diffs
    sql_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    saved_query: SavedQuery = Relationship(back_populates="runs")

class QueryComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    saved_query_id: int = Field(foreign_key="savedquery.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    body: str
    is_edited: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    saved_query: SavedQuery = Relationship(back_populates="comments")
