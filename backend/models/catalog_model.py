from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from .db_model import UserDatabase
    from .tenant_model import Workspace

class CatalogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class MetricStatus(str, Enum):
    DRAFT = "draft"
    CERTIFIED = "certified"

class CatalogEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    db_id: int = Field(foreign_key="userdatabase.id", index=True)
    
    table_name: str = Field(index=True)
    description: Optional[str] = None
    owner: Optional[str] = None
    freshness: Optional[datetime] = None
    status: CatalogStatus = Field(default=CatalogStatus.DRAFT)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    column_annotations: List["ColumnAnnotation"] = Relationship(back_populates="catalog_entry")

class ColumnAnnotation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    catalog_entry_id: int = Field(foreign_key="catalogentry.id", index=True)
    
    column_name: str = Field(index=True)
    description: Optional[str] = None
    sensitivity_label: Optional[str] = None # e.g. PII, Restricted
    
    catalog_entry: CatalogEntry = Relationship(back_populates="column_annotations")

class BusinessTerm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    term: str = Field(index=True)
    definition: str
    synonyms: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Mapping metadata
    maps_to_table: Optional[str] = None
    maps_to_column: Optional[str] = None
    
    certified_by: Optional[int] = Field(default=None, foreign_key="user.id")
    certified_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MetricDefinition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    sql_expression: str # e.g. SUM(amount)
    owner: Optional[str] = None
    
    status: MetricStatus = Field(default=MetricStatus.DRAFT)
    certified_by: Optional[int] = Field(default=None, foreign_key="user.id")
    certified_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
