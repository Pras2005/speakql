from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user_model import User
    from .query_model import QueryHistory
    from .tenant_model import Workspace, DatabaseAccessGrant

# Explicit import for SQLModel mapper to resolve relationships during combined test runs
from .user_model import User
from .tenant_model import Workspace, DatabaseAccessGrant

class UserDatabase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    host: Optional[str] = None
    port: Optional[int] = None
    db_user: Optional[str] = None
    db_password_encrypted: str
    db_name: str
    mcp_api_key: Optional[str] = Field(default=None, index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Health status persistence
    last_health_status: Optional[str] = None
    last_health_check_at: Optional[datetime] = None
    health_failure_summary: Optional[str] = None

    owner: "User" = Relationship(back_populates="databases")
    workspace: "Workspace" = Relationship(back_populates="databases")
    access_grants: List["DatabaseAccessGrant"] = Relationship(back_populates="database")
    history: List["QueryHistory"] = Relationship(
        back_populates="database", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
