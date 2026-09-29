from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING


if TYPE_CHECKING:
    from .db_model import UserDatabase
    from .tenant_model import Membership, DatabaseAccessGrant

# Explicit import for SQLModel mapper to resolve relationships during combined test runs
from .tenant_model import Membership, DatabaseAccessGrant

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    token_version: int = Field(default=1)

    databases: List["UserDatabase"] = Relationship(back_populates="owner")
    memberships: List["Membership"] = Relationship(back_populates="user")
    database_access_grants: List["DatabaseAccessGrant"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "DatabaseAccessGrant.user_id"}
    )
    granted_database_access: List["DatabaseAccessGrant"] = Relationship(
        back_populates="grantor",
        sa_relationship_kwargs={"foreign_keys": "DatabaseAccessGrant.granted_by"}
    )
