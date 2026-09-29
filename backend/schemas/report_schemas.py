from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReportCreate(BaseModel):
    name: str
    saved_query_id: int
    database_id: int
    schedule_cron: str
    delivery_config: Dict[str, Any]
    is_enabled: bool = True

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    saved_query_id: Optional[int] = None
    database_id: Optional[int] = None
    schedule_cron: Optional[str] = None
    delivery_config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

class ReportResponse(BaseModel):
    id: int
    workspace_id: int
    saved_query_id: int
    database_id: int
    name: str
    schedule_cron: str
    delivery_config: Dict[str, Any]
    is_enabled: bool
    last_ran_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportRunResponse(BaseModel):
    id: int
    report_id: int
    workspace_id: int
    status: str
    executed_at: datetime
    audit_event_id: Optional[int] = None
    error_message: Optional[str] = None
    delivery_outcome: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class RunReportRequest(BaseModel):
    db_id: int
