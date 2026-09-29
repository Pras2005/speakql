from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .db_model import UserDatabase

class QueryHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_database_id: int = Field(foreign_key="userdatabase.id", index=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    event_type: str = Field(default="execution")
    original_prompt: Optional[str] = None
    generated_sql: Optional[str] = None
    executed_sql: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)

    database: "UserDatabase" = Relationship(
        back_populates="history",
        sa_relationship_kwargs={"passive_deletes": True}
    ) 
