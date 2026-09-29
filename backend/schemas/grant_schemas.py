from datetime import datetime

from sqlmodel import SQLModel

from models.tenant_model import DatabaseAccessLevel


class DatabaseGrantCreate(SQLModel):
    user_id: int
    access_level: DatabaseAccessLevel


class DatabaseGrantUpdate(SQLModel):
    access_level: DatabaseAccessLevel


class DatabaseGrantRead(SQLModel):
    id: int
    workspace_id: int
    database_id: int
    user_id: int
    access_level: DatabaseAccessLevel
    granted_by: int
    created_at: datetime
    updated_at: datetime
