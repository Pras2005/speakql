from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from .tenant_model import MembershipRole

class WorkspaceApiKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True) # The "Actor" (Service Account or User)
    
    name: str = Field(index=True)
    key_prefix: str = Field(index=True) # To help identify the key (e.g. sk_live_...)
    hashed_key: str = Field(unique=True, index=True)
    
    # Default database to use for this key if no db_id provided in MCP call
    default_db_id: Optional[int] = Field(default=None, foreign_key="userdatabase.id")
    
    role: MembershipRole = Field(default=MembershipRole.ANALYST)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
