from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.catalog_model import CatalogStatus, MetricStatus

class CatalogEntryResponse(BaseModel):
    id: int
    workspace_id: int
    db_id: int
    table_name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    freshness: Optional[datetime] = None
    status: CatalogStatus
    
    class Config:
        from_attributes = True

class PublishTableRequest(BaseModel):
    db_id: int
    table_name: str
    description: str

class BusinessTermCreate(BaseModel):
    term: str
    definition: str
    maps_to_table: Optional[str] = None
    maps_to_column: Optional[str] = None

class BusinessTermResponse(BaseModel):
    id: int
    term: str
    definition: str
    maps_to_table: Optional[str] = None
    maps_to_column: Optional[str] = None
    
    class Config:
        from_attributes = True

class MetricDefinitionCreate(BaseModel):
    name: str
    sql_expression: str
    description: Optional[str] = None

class MetricDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    sql_expression: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MetricStatus] = None

class MetricDefinitionResponse(BaseModel):
    id: int
    name: str
    sql_expression: str
    description: Optional[str] = None
    status: MetricStatus
    
    class Config:
        from_attributes = True
