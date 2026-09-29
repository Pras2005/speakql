import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.workflow_service import WorkflowService
from services.report_service import ReportService
from models.workflow_model import SavedQuery, SavedQueryStatus, QueryComment
from models.report_model import Report
from core.request_context import RequestContext, set_request_context
from datetime import datetime

@pytest.mark.asyncio
async def test_review_rejection_path():
    query_repo = MagicMock()
    # Mock update_query internal call via update
    query_repo.get_by_id = AsyncMock(return_value=SavedQuery(id=1, status=SavedQueryStatus.SUBMITTED, workspace_id=1))
    query_repo.update = AsyncMock(side_effect=lambda x: x)
    
    gov_service = MagicMock()
    gov_service.db_service.audit_service.record_event = AsyncMock()
    
    service = WorkflowService(query_repo, MagicMock(), gov_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    result = await service.reject_query(query_id=1, reviewer_id=99, reason="Insecure SQL")
    
    assert result.status == SavedQueryStatus.REJECTED
    assert result.review_reason == "Insecure SQL"
    assert result.reviewed_by == 99
    assert gov_service.db_service.audit_service.record_event.called

@pytest.mark.asyncio
async def test_archive_transition():
    query_repo = MagicMock()
    query_repo.get_by_id = AsyncMock(return_value=SavedQuery(id=1, status=SavedQueryStatus.APPROVED, workspace_id=1))
    query_repo.update = AsyncMock(side_effect=lambda x: x)
    
    gov_service = MagicMock()
    gov_service.db_service.audit_service.record_event = AsyncMock()
    
    service = WorkflowService(query_repo, MagicMock(), gov_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    result = await service.archive_query(query_id=1)
    
    assert result.status == SavedQueryStatus.ARCHIVED
    assert gov_service.db_service.audit_service.record_event.called

@pytest.mark.asyncio
async def test_comment_ownership_and_edit():
    comment_repo = MagicMock()
    # Comment owned by user 10
    comment = QueryComment(id=5, user_id=10, body="Original", workspace_id=1)
    comment_repo.get_by_id = AsyncMock(return_value=comment)
    comment_repo.update = AsyncMock(side_effect=lambda x: x)
    
    service = WorkflowService(MagicMock(), comment_repo, MagicMock())
    
    # Try edit by owner
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    updated = await service.update_comment(comment_id=5, body="Updated")
    assert updated.body == "Updated"
    
    # Try edit by someone else
    set_request_context(RequestContext(workspace_id=1, user_id=11))
    with pytest.raises(ValueError, match="Only the author can edit this comment"):
        await service.update_comment(comment_id=5, body="Hacked")

@pytest.mark.asyncio
async def test_slack_delivery_adapter():
    report_repo = MagicMock()
    report_repo.get_by_id = AsyncMock(return_value=Report(
        id=1, 
        workspace_id=1, 
        database_id=2, 
        saved_query_id=10,
        delivery_config={"slack_channel": "#alerts", "email": "admin@example.com"}
    ))
    report_repo.update = AsyncMock()
    
    run_repo = MagicMock()
    run_repo.create = AsyncMock(side_effect=lambda x: x)
    
    workflow_service = MagicMock()
    workflow_service.get_query = AsyncMock(return_value=MagicMock(status=SavedQueryStatus.APPROVED))
    workflow_service.replay_query = AsyncMock(return_value={"status": "success", "query_id": 100})
    
    audit_service = MagicMock()
    audit_service.record_event = AsyncMock() # Must be AsyncMock
    
    service = ReportService(report_repo, run_repo, workflow_service, audit_service)
    set_request_context(RequestContext(workspace_id=1, user_id=10))
    
    run = await service.run_report(report_id=1, db_id=2, agent_tools=MagicMock())
    
    assert run.delivery_outcome["slack"] == "posted_to_#alerts"
    assert run.delivery_outcome["email"] == "sent"
    assert run.delivery_outcome["delivered"] is True

@pytest.mark.asyncio
async def test_report_scheduler_scoping():
    # Test that run_pending_reports uses the database_id from the report
    report_repo = MagicMock()
    
    report1 = Report(id=1, workspace_id=1, database_id=10, is_enabled=True, last_ran_at=None, delivery_config={}, saved_query_id=1)
    report2 = Report(id=2, workspace_id=1, database_id=20, is_enabled=True, last_ran_at=None, delivery_config={}, saved_query_id=2)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [report1, report2]
    report_repo.session.execute = AsyncMock(return_value=mock_result)
    
    db_repo = MagicMock()
    db_repo.get_by_id = AsyncMock(side_effect=lambda db_id: MagicMock(id=db_id))
    
    # Mock AIService and DatabaseAgent to avoid real imports/calls
    with patch("services.ai_service.AIService") as mock_ai:
        with patch("utils.agent.DatabaseAgent") as mock_agent:
            service = ReportService(report_repo, MagicMock(), MagicMock(), MagicMock())
            
            with patch.object(service, 'run_report', AsyncMock()) as mock_run:
                await service.run_pending_reports(db_repo)
                
                assert mock_run.call_count == 2
                # Check it was called with correct db_ids
                args1 = mock_run.call_args_list[0][0]
                assert args1[1] == 10
                args2 = mock_run.call_args_list[1][0]
                assert args2[1] == 20
