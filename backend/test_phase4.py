import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.workflow_service import WorkflowService
from services.catalog_service import CatalogService
from models.workflow_model import SavedQuery, SavedQueryVisibility, SavedQueryStatus
from models.catalog_model import BusinessTerm, MetricDefinition
from core.request_context import RequestContext, set_request_context

@pytest.mark.asyncio
async def test_saved_query_creation():
    repo = MagicMock()
    repo.create = AsyncMock(return_value=SavedQuery(id=1, name="Test Query"))
    
    gov_service = MagicMock()
    gov_service.db_service.audit_service.record_event = AsyncMock()
    
    service = WorkflowService(repo, MagicMock(), gov_service)
    
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    result = await service.save_query(name="Test Query", sql="SELECT 1")
    assert result.id == 1
    assert repo.create.called
    assert gov_service.db_service.audit_service.record_event.called

@pytest.mark.asyncio
async def test_sql_diff_logic():
    service = WorkflowService(MagicMock(), MagicMock(), MagicMock())
    
    sql_a = "SELECT name FROM users WHERE id = 1"
    sql_b = "SELECT name, email FROM users JOIN accounts ON users.id = accounts.user_id WHERE id = 1 GROUP BY name"
    
    diff = await service.compute_sql_diff(sql_a, sql_b)
    
    assert "added_tables" in diff
    assert "accounts" in diff["added_tables"]
    assert diff["clause_changes"]["group_by"] is True
    assert diff["clause_changes"]["where"] is False # Both have where

@pytest.mark.asyncio
async def test_semantic_context_generation():
    glossary_repo = MagicMock()
    glossary_repo.list_by_workspace = AsyncMock(return_value=[
        BusinessTerm(term="AUM", definition="Assets Under Management", maps_to_table="holdings")
    ])
    metric_repo = MagicMock()
    metric_repo.list_by_workspace = AsyncMock(return_value=[
        MetricDefinition(name="total_revenue", sql_expression="SUM(amount)", status="certified")
    ])
    
    service = CatalogService(MagicMock(), glossary_repo, metric_repo)
    set_request_context(RequestContext(workspace_id=1))
    
    context = await service.get_semantic_context()
    assert "BUSINESS GLOSSARY" in context
    assert "AUM" in context
    assert "total_revenue" in context
    assert "SUM(amount)" in context

@pytest.mark.asyncio
async def test_replay_query_governance_integration():
    query_repo = MagicMock()
    query_repo.get_by_id = AsyncMock(return_value=SavedQuery(id=1, name="Q1", sql="SELECT 1", workspace_id=1))
    query_repo.create_run = AsyncMock()
    
    gov_service = MagicMock()
    gov_service.execute_governed_query = AsyncMock(return_value={"status": "success", "result": [{"id": 1}], "query_id": 100})
    gov_service.db_service.audit_service.record_event = AsyncMock()
    
    service = WorkflowService(query_repo, MagicMock(), gov_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    result = await service.replay_query(query_id=1, db_id=2, agent_tools=MagicMock())
    
    assert result["status"] == "success"
    assert gov_service.execute_governed_query.called
    assert query_repo.create_run.called
    assert gov_service.db_service.audit_service.record_event.called

@pytest.mark.asyncio
async def test_report_manual_run():
    report_repo = MagicMock()
    report_repo.get_by_id = AsyncMock(return_value=MagicMock(id=1, saved_query_id=10, workspace_id=1, delivery_config={}))
    report_repo.update = AsyncMock()
    
    run_repo = MagicMock()
    run_repo.create = AsyncMock(return_value=MagicMock(id=100))
    
    workflow_service = MagicMock()
    workflow_service.get_query = AsyncMock(return_value=MagicMock(id=10, status=SavedQueryStatus.APPROVED))
    workflow_service.replay_query = AsyncMock(return_value={"status": "success", "query_id": 500})
    
    audit_service = MagicMock()
    audit_service.record_event = AsyncMock()
    
    from services.report_service import ReportService
    service = ReportService(report_repo, run_repo, workflow_service, audit_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    result = await service.run_report(report_id=1, db_id=2, agent_tools=MagicMock())
    
    assert result.id == 100
    assert workflow_service.replay_query.called
    assert report_repo.update.called
    assert audit_service.record_event.called

@pytest.mark.asyncio
async def test_catalog_draft_generation():
    catalog_repo = MagicMock()
    catalog_repo.get_by_table = AsyncMock(return_value=None)
    catalog_repo.create = AsyncMock()
    
    audit_service = MagicMock()
    audit_service.record_event = AsyncMock()
    
    service = CatalogService(catalog_repo, MagicMock(), MagicMock(), audit_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    await service.generate_draft_catalog(db_id=1, tables=["users", "orders"])
    
    assert catalog_repo.create.call_count == 2
    assert audit_service.record_event.called

@pytest.mark.asyncio
async def test_metric_lifecycle():
    metric_repo = MagicMock()
    metric_repo.create = AsyncMock(return_value=MetricDefinition(id=1, name="m1"))
    metric_repo.get_by_id = AsyncMock(return_value=MetricDefinition(id=1, name="m1", workspace_id=1))
    
    session = AsyncMock()
    session.get = AsyncMock(return_value=MetricDefinition(id=1, name="m1"))
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    
    catalog_repo = MagicMock()
    catalog_repo.session = session
    
    audit_service = MagicMock()
    audit_service.record_event = AsyncMock()
    
    service = CatalogService(catalog_repo, MagicMock(), metric_repo, audit_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    # Create
    m = await service.create_metric(name="m1", expression="SUM(1)")
    assert m.id == 1
    
    # Delete
    success = await service.delete_metric(metric_id=1)
    assert success is True
    assert session.delete.called
    assert audit_service.record_event.called
