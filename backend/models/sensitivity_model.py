from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class SensitivityLabel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"

class MaskingStrategy(str, Enum):
    REDACT = "redact"          # Full redaction (e.g., "REDACTED")
    PARTIAL = "partial_mask"   # Partial (e.g., "v***@email.com")
    HASH = "hash"              # Deterministic hash
    NONE = "none"              # No masking

class SensitivityRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    
    # Scope
    table_name: str = Field(index=True)
    column_name: str = Field(index=True)
    
    # Metadata
    label: SensitivityLabel = Field(default=SensitivityLabel.INTERNAL)
    masking_strategy: MaskingStrategy = Field(default=MaskingStrategy.NONE)
    priority: int = Field(default=0)
    active: bool = Field(default=True)
    
    # Optional role-based overrides (e.g., ["viewer", "analyst"])
    # If empty, applies to everyone. If populated, applies only to these roles.
    restricted_roles: List[str] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
