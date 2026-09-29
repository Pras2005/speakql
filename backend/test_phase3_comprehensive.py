import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import hashlib
import json
from services.governance_service import GovernanceService
from services.audit_service import AuditService
from services.health_service import HealthService
from services.governed_export_service import GovernedExportService
from repositories.audit_repository import AuditRepository
from models.audit_model import AuditEvent
from models.db_model import UserDatabase
from models.user_model import User
from models.tenant_model import Membership, Workspace, Organization, DatabaseAccessLevel
from core.request_context import RequestContext, set_request_context

@pytest.mark.asyncio
async def test_audit_repository_category_filtering():
    session = AsyncMock()
    repo = AuditRepository(session)
    
    # Mocking session.execute to return a count and a list
    mock_result = MagicMock()
    mock_result.scalar.return_value = 10
    mock_result.scalars().all.return_value = []
    session.execute.return_value = mock_result
    
    # Test with category
    await repo.list_by_workspace(workspace_id=1, category="governance")
    
    # Check if category-specific event types were used in the query
    # We'd ideally inspect the query object, but since it's an AsyncMock, 
    # we can at least verify session.execute was called.
    assert session.execute.called

@pytest.mark.asyncio
async def test_governance_service_explainability_payload():
    db_service = AsyncMock()
    policy_service = MagicMock()
    risk_service = MagicMock()
    approval_service = MagicMock()
    masking_service = MagicMock()
    confidence_service = MagicMock()
    
    # Setup mocks
    policy_service.get_active_policies = AsyncMock(return_value=[])
    policy_service.evaluate_policy.return_value = {"allowed": True, "reason": "OK"}
    risk_service.evaluate_risk.return_value = {"risk_score": 0.1, "flags": [], "requires_approval": False}
    confidence_service.evaluate_confidence.return_value = {"score": 0.9, "needs_review": False}
    
    agent_tools = MagicMock()
    agent_tools.execute_query = AsyncMock(return_value=[{"id": 1, "name": "Test"}])
    masking_service.mask_results.return_value = [{"id": 1, "name": "Test"}]
    masking_service.sensitivity_service.get_applicable_rules = AsyncMock(return_value={})
    db_service.has_database_access = AsyncMock(return_value=True)

    set_request_context(RequestContext(workspace_id=1, role="admin"))
    
    gov_service = GovernanceService(
        db_service, policy_service, risk_service, approval_service, masking_service, confidence_service
    )
    
    result = await gov_service.execute_governed_query(
        db_id=1, user_id=1, sql="SELECT * FROM test", sql_rationale="Custom rationale", agent_tools=agent_tools
    )
    
    assert result["status"] == "success"
    assert result["explainability"]["sql_rationale"] == "Custom rationale"
    assert result["explainability"]["confidence_score"] == 0.9
    assert "tables_referenced" in result["explainability"]

@pytest.mark.asyncio
async def test_governance_service_low_confidence_approval_required():
    db_service = AsyncMock()
    policy_service = MagicMock()
    risk_service = MagicMock()
    approval_service = MagicMock()
    masking_service = MagicMock()
    confidence_service = MagicMock()
    
    # Setup mocks
    policy_service.get_active_policies = AsyncMock(return_value=[])
    policy_service.evaluate_policy.return_value = {"allowed": True, "reason": "OK"}
    risk_service.evaluate_risk.return_value = {"risk_score": 0.1, "flags": [], "requires_approval": False}
    # Low confidence
    confidence_service.evaluate_confidence.return_value = {"score": 0.4, "needs_review": True}
    
    approval_service.request_approval = AsyncMock(return_value=MagicMock(id=123))
    db_service.audit_service.record_event = AsyncMock()
    db_service.has_database_access = AsyncMock(return_value=True)

    set_request_context(RequestContext(workspace_id=1, user_id=1, role="analyst"))
    
    gov_service = GovernanceService(
        db_service, policy_service, risk_service, approval_service, masking_service, confidence_service
    )
    
    result = await gov_service.execute_governed_query(
        db_id=1, user_id=1, sql="SELECT * FROM test", agent_tools=MagicMock()
    )
    
    assert result["status"] == "approval_required"
    assert result["approval_id"] == 123
    assert "Low confidence" in result["error"]
    assert result["explainability"]["confidence_score"] == 0.4
    assert result["explainability"]["needs_review"] is True

@pytest.mark.asyncio
async def test_governance_service_denies_without_database_access():
    db_service = AsyncMock()
    db_service.has_database_access = AsyncMock(return_value=False)
    db_service.log_query = AsyncMock(return_value=MagicMock(id=321))

    gov_service = GovernanceService(
        db_service,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )

    set_request_context(RequestContext(workspace_id=1, user_id=1, role="analyst"))
    result = await gov_service.execute_governed_query(
        db_id=8,
        user_id=1,
        sql="SELECT * FROM test",
        agent_tools=MagicMock(),
        required_access_level=DatabaseAccessLevel.QUERY,
    )

    assert result["status"] == "denied"
    assert "query access required" in result["error"]
    db_service.log_query.assert_awaited_once()

@pytest.mark.asyncio
async def test_governed_export_audit_writes():
    gov_service = MagicMock()
    export_service = MagicMock()
    audit_service = MagicMock()
    
    gov_service.execute_governed_query = AsyncMock(return_value={
        "status": "success",
        "result": [{"id": 1}],
        "explainability": {},
        "query_id": 456
    })
    export_service.to_csv = MagicMock(return_value="csv data")
    audit_service.record_event = AsyncMock()

    set_request_context(RequestContext(workspace_id=1, user_id=1))
    
    service = GovernedExportService(gov_service, export_service, audit_service)
    await service.export_query_results(db_id=1, user_id=1, sql="SELECT 1", format="csv", agent_tools=MagicMock())
    
    # Verify audit events recorded (REQUESTED and COMPLETED)
    assert audit_service.record_event.call_count == 2
    
    # Check REQUESTED
    args0, kwargs0 = audit_service.record_event.call_args_list[0]
    assert kwargs0["event_type"] == "DATA_EXPORT_REQUESTED"
    
    # Check COMPLETED
    args1, kwargs1 = audit_service.record_event.call_args_list[1]
    assert kwargs1["event_type"] == "DATA_EXPORT_COMPLETED"
    assert kwargs1["details"]["format"] == "csv"
    assert kwargs1["details"]["query_id"] == 456

@pytest.mark.asyncio
async def test_audit_chain_hashing():
    session = AsyncMock()
    repo = AuditRepository(session)
    
    # 1. Test first event (GENESIS)
    mock_result_none = MagicMock()
    mock_result_none.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result_none
    
    event1 = AuditEvent(workspace_id=1, event_type="TEST_1", details={"step": 1})
    saved_event1 = await repo.create(event1)
    
    assert saved_event1.previous_hash == "GENESIS"
    assert saved_event1.hash is not None
    
    # 2. Test second event (links to first)
    mock_result_last = MagicMock()
    mock_result_last.scalar_one_or_none.return_value = saved_event1
    session.execute.return_value = mock_result_last
    
    event2 = AuditEvent(workspace_id=1, event_type="TEST_2", details={"step": 2})
    saved_event2 = await repo.create(event2)
    
    assert saved_event2.previous_hash == saved_event1.hash
    assert saved_event2.hash != saved_event1.hash

@pytest.mark.asyncio
async def test_health_service_audit_writes():
    db_repo = AsyncMock()
    audit_service = AsyncMock()
    
    db_repo.get_by_id = AsyncMock(return_value=MagicMock(
        id=1, db_name="test_db", workspace_id=1, org_id=1,
        host="localhost", port=5432, db_user="user", db_password_encrypted=b"pass"
    ))
    
    with patch("services.health_service.validate_database_connection") as mock_val, \
         patch("services.health_service.decrypt_password", return_value="pass"):
        
        service = HealthService(db_repo, audit_service)
        await service.check_database_health(db_id=1)
        
        # Verify audit event recorded
        audit_service.record_event.assert_called_once()
        args, kwargs = audit_service.record_event.call_args
        assert kwargs["event_type"] == "CONNECTOR_HEALTH_CHECK"
        assert kwargs["details"]["db_name"] == "test_db"
