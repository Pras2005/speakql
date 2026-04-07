from typing import Optional
from sqlmodel import SQLModel
from datetime import datetime


class UserDatabaseCreate(SQLModel):
    host: Optional[str] = None
    port: Optional[int] = None
    db_user: Optional[str] = None
    db_password: str
    db_name: str


class UserDatabaseRead(SQLModel):
    id: int
    user_id: int
    host: Optional[str] = None
    port: Optional[int] = None
    db_user: Optional[str] = None
    db_name: str
    name: Optional[str] = None # Alias for db_name to match frontend
    created_at: datetime

class UserDatabaseUpdate(SQLModel):  # New class added for update operations
    host: Optional[str] = None
    port: Optional[int] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: Optional[str] = None
