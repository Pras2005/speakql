from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .user_model import User
    from .db_model import UserDatabase

class MembershipRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    COMPLIANCE_ADMIN = "compliance_admin"

class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workspaces: List["Workspace"] = Relationship(back_populates="organization")

class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(back_populates="workspaces")
    memberships: List["Membership"] = Relationship(back_populates="workspace")
    databases: List["UserDatabase"] = Relationship(back_populates="workspace")

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: MembershipRole = Field(default=MembershipRole.VIEWER)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workspace: Workspace = Relationship(back_populates="memberships")
    user: "User" = Relationship(back_populates="memberships")
