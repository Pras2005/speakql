from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PolicyOutcome(BaseModel):
    allowed: bool
    reason: str
    policy_id: Optional[int] = None

class RiskMetadata(BaseModel):
    score: float
    flags: List[str]

class ExplainabilityPayload(BaseModel):
    sql_rationale: Optional[str] = None
    tables_referenced: List[str]
    policy_outcome: PolicyOutcome
    risk_metadata: RiskMetadata
    confidence_score: float  # 0.0 to 1.0
    needs_review: bool

class GovernedQueryResponse(BaseModel):
    status: str
    result: Optional[List[Dict[str, Any]]] = None
    explainability: ExplainabilityPayload
    error: Optional[str] = None

# --- Admin Trust Surface Schemas ---

class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int = 0
    rules: Dict[str, Any]

class PolicyResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    priority: int
    rules_json: Dict[str, Any]

    class Config:
        from_attributes = True

class SensitivityRuleCreate(BaseModel):
    table_name: str
    column_name: str
    label: str = "internal"
    masking_strategy: str = "none"
    priority: int = 0
    restricted_roles: List[str] = []

class SensitivityRuleResponse(BaseModel):
    id: int
    workspace_id: int
    table_name: str
    column_name: str
    label: str
    masking_strategy: str
    priority: int
    restricted_roles: List[str]

    class Config:
        from_attributes = True

class ConnectorHealthResponse(BaseModel):
    id: int
    db_name: str
    status: str
    last_check: Optional[str]
    error: Optional[str] = None
