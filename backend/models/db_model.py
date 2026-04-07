from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class UserDatabase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") 
    host: Optional[str] = None
    port: Optional[int] = None
    db_user: Optional[str] = None
    db_password_encrypted: str
    db_name: str
    mcp_api_key: Optional[str] = Field(default=None, index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner: "User" = Relationship(back_populates="databases")
    history: List["QueryHistory"] = Relationship(back_populates="database", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

