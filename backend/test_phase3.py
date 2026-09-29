import pytest
from services.sensitivity_service import SensitivityService
from services.masking_service import MaskingService
from services.confidence_service import ConfidenceService
from models.sensitivity_model import SensitivityRule, MaskingStrategy, SensitivityLabel
from models.user_model import User
from models.db_model import UserDatabase
from models.tenant_model import Membership, Workspace, Organization

def test_sensitivity_resolution():
    rules = [
        SensitivityRule(column_name="email", masking_strategy=MaskingStrategy.REDACT, priority=10),
        SensitivityRule(column_name="email", masking_strategy=MaskingStrategy.PARTIAL, priority=5, restricted_roles=["viewer"])
    ]
    service = SensitivityService(None)
    
    # 1. Higher priority wins
    strategy = service.resolve_masking_requirement(rules, "email", "admin")
    assert strategy == MaskingStrategy.REDACT
    
    # 2. No rule matches
    strategy = service.resolve_masking_requirement(rules, "name", "admin")
    assert strategy == MaskingStrategy.NONE

def test_masking_strategies():
    service = MaskingService(None)
    
    # Redact
    assert service._apply_strategy("secret", MaskingStrategy.REDACT) == "[REDACTED]"
    
    # Hash
    hashed = service._apply_strategy("secret", MaskingStrategy.HASH)
    assert len(hashed) == 16
    assert hashed != "secret"
    
    # Partial
    assert service._apply_strategy("test@example.com", MaskingStrategy.PARTIAL) == "te****om"
    assert service._apply_strategy("abc", MaskingStrategy.PARTIAL) == "****"

def test_confidence_scoring():
    service = ConfidenceService()
    
    # High confidence
    res = service.evaluate_confidence("SELECT * FROM users")
    assert res["score"] >= 0.8
    assert res["needs_review"] is False
    
    # Lower confidence due to many joins
    complex_sql = "SELECT * FROM a JOIN b ON a.id=b.id JOIN c ON b.id=c.id JOIN d ON c.id=d.id JOIN e ON d.id=e.id JOIN f ON e.id=f.id JOIN g ON f.id=g.id"
    res = service.evaluate_confidence(complex_sql)
    assert res["score"] < 0.8

def test_result_masking_logic():
    sensitivity_service = SensitivityService(None)
    masking_service = MaskingService(sensitivity_service)
    
    rules = {
        "users": [
            SensitivityRule(column_name="email", masking_strategy=MaskingStrategy.REDACT),
            SensitivityRule(column_name="phone", masking_strategy=MaskingStrategy.PARTIAL)
        ]
    }
    
    results = [
        {"id": 1, "email": "user1@test.com", "phone": "1234567890", "name": "User One"}
    ]
    
    masked = masking_service.mask_results(results, rules, "viewer")
    
    assert masked[0]["id"] == 1
    assert masked[0]["email"] == "[REDACTED]"
    assert masked[0]["phone"] == "12****90"
    assert masked[0]["name"] == "User One"
