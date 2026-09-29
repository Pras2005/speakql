from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from .user_model import User
    from .db_model import UserDatabase
    from .mcp_model import WorkspaceApiKey

class MembershipRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    COMPLIANCE_ADMIN = "compliance_admin"


class DatabaseAccessLevel(str, Enum):
    DISCOVER = "discover"
    QUERY = "query"
    EXPORT = "export"
    MANAGE = "manage"

class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    workspaces: List["Workspace"] = Relationship(back_populates="organization")

class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    organization: Organization = Relationship(back_populates="workspaces")
    memberships: List["Membership"] = Relationship(back_populates="workspace")
    databases: List["UserDatabase"] = Relationship(back_populates="workspace")
    database_access_grants: List["DatabaseAccessGrant"] = Relationship(back_populates="workspace")
    api_keys: List["WorkspaceApiKey"] = Relationship(
        sa_relationship_kwargs={"backref": "workspace", "cascade": "all, delete-orphan"}
    )

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: MembershipRole = Field(default=MembershipRole.VIEWER)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workspace: Workspace = Relationship(back_populates="memberships")
    user: "User" = Relationship(back_populates="memberships")


class DatabaseAccessGrant(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("workspace_id", "database_id", "user_id", name="uq_db_access_grant_scope"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    database_id: int = Field(foreign_key="userdatabase.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    access_level: DatabaseAccessLevel
    granted_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    workspace: Workspace = Relationship(back_populates="database_access_grants")
    database: "UserDatabase" = Relationship(back_populates="access_grants")
    user: "User" = Relationship(
        back_populates="database_access_grants",
        sa_relationship_kwargs={"foreign_keys": "DatabaseAccessGrant.user_id"},
    )
    grantor: "User" = Relationship(
        back_populates="granted_database_access",
        sa_relationship_kwargs={"foreign_keys": "DatabaseAccessGrant.granted_by"},
    )


# Explicit import for SQLModel mapper to resolve relationships during combined test runs
from .mcp_model import WorkspaceApiKey
