import importlib
import sys
import types

import pytest

from core.request_context import RequestContext, set_request_context
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from services.policy_service import PolicyService
from services.risk_service import RiskScoringService
from services.database_service import DatabaseService
from models.tenant_model import Membership, Organization, Workspace, DatabaseAccessLevel
from utils.sql_safety import validate_sql_safety, extract_tables
from models.policy_model import Policy
from models.user_model import User

def test_ast_validation():
    # Valid Select
    assert validate_sql_safety("SELECT * FROM users") is None
    # Blocked Update
    err = validate_sql_safety("UPDATE users SET admin = true")
    assert "not allowed" in err.lower()
    # Blocked Multi-statement
    err = validate_sql_safety("SELECT 1; DROP TABLE users")
    assert "single-statement" in err.lower()
    # Syntax Error
    err = validate_sql_safety("SELECT FROM")
    assert "syntax error" in err.lower()

def test_table_extraction():
    tables = extract_tables("SELECT u.name, o.id FROM users u JOIN orders o ON u.id = o.user_id")
    assert "users" in tables
    assert "orders" in tables

def test_policy_evaluation():
    policy = Policy(
        name="Test Policy",
        rules_json={
            "blocked_tables": ["secrets"],
            "row_limit": 100
        }
    )
    service = PolicyService(None)
    
    # 1. Blocked table
    context = {"sql": "SELECT * FROM secrets", "tables": {"secrets"}}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is False
    assert "blocked" in decision["reason"].lower()
    
    # 2. Row limit
    context = {"sql": "SELECT * FROM users", "tables": {"users"}}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is True
    assert decision["limit_rows"] == 100

def test_role_policy():
    policy = Policy(
        name="Role Policy",
        rules_json={"restricted_roles": ["viewer"]}
    )
    service = PolicyService(None)
    
    # 1. Deny viewer
    context = {"user_role": "viewer"}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is False
    assert "viewer" in decision["reason"]
    
    # 2. Allow analyst
    context = {"user_role": "analyst"}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is True

def test_schema_policy():
    policy = Policy(
        name="Schema Policy",
        rules_json={"allowed_schemas": ["public", "analytics"]}
    )
    service = PolicyService(None)
    
    # 1. Allow public
    context = {"tables": {"public.users"}}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is True
    
    # 2. Deny raw_data
    context = {"tables": {"raw_data.logs"}}
    decision = service.evaluate_policy([policy], context)
    assert decision["allowed"] is False
    assert "raw_data" in decision["reason"]

def test_timeout_policy():
    policy1 = Policy(name="T1", rules_json={"execution_timeout": 30})
    policy2 = Policy(name="T2", rules_json={"execution_timeout": 10})
    service = PolicyService(None)
    
    # Cumulative - should take the minimum
    decision = service.evaluate_policy([policy1, policy2], {})
    assert decision["timeout"] == 10


def test_risk_scoring():
    service = RiskScoringService()
    
    # Low risk
    risk = service.evaluate_risk("SELECT name FROM users WHERE id = 1")
    assert risk["risk_score"] < 0.5
    assert risk["requires_approval"] is False
    
    # High risk: SELECT * without WHERE
    risk = service.evaluate_risk("SELECT * FROM large_table")
    assert risk["risk_score"] >= 0.5
    assert "FULL_COLUMN_SCAN" in risk["flags"]
    assert "NO_WHERE_CLAUSE" in risk["flags"]
    
    # Very high risk: pg_sleep
    risk = service.evaluate_risk("SELECT pg_sleep(10)")
    assert risk["requires_approval"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_denied_query_writes_execution_denied_audit():
    class FakeDbRepo:
        async def add_query_history(self, history):
            return history

    class FakeAuditService:
        def __init__(self):
            self.calls = []

        async def record_event(self, **kwargs):
            self.calls.append(kwargs)
            return kwargs

    set_request_context(
        RequestContext(
            request_id="req-phase2-audit",
            user_id=7,
            org_id=11,
            workspace_id=13,
            role="analyst",
        )
    )

    audit_service = FakeAuditService()
    service = DatabaseService(FakeDbRepo(), audit_service)
    await service.log_query(
        db_id=17,
        user_id=7,
        event_type="execution",
        prompt="show secrets",
        executed_sql="SELECT * FROM secrets",
        success=False,
        error="Policy Denied: Table 'secrets' is blocked by policy 'prod-policy'",
    )

    assert len(audit_service.calls) == 1
    assert audit_service.calls[0]["event_type"] == "EXECUTION_DENIED"
    assert audit_service.calls[0]["user_id"] == 7
    assert audit_service.calls[0]["details"]["database_id"] == 17
    assert "Policy Denied" in audit_service.calls[0]["details"]["error"]


@pytest.mark.asyncio(loop_scope="function")
async def test_get_databases_filters_by_grants():
    class FakeDbRepo:
        async def list_by_ids(self, workspace_id, database_ids):
            return [UserDatabase(id=db_id, user_id=1, org_id=11, workspace_id=workspace_id, db_password_encrypted="x", db_name=f"db_{db_id}") for db_id in database_ids]

    class FakeGrantService:
        async def list_database_ids_for_user(self, user_id):
            return [2, 5]

    set_request_context(RequestContext(user_id=7, org_id=11, workspace_id=13, role="analyst"))

    service = DatabaseService(FakeDbRepo(), audit_service=object(), grant_service=FakeGrantService())
    dbs = await service.get_databases(user_id=7)

    assert [db.id for db in dbs] == [2, 5]


@pytest.mark.asyncio(loop_scope="function")
async def test_add_database_creates_manage_grant_for_creator():
    class FakeDbRepo:
        async def create(self, db):
            db.id = 99
            return db

    class FakeGrantService:
        def __init__(self):
            self.calls = []

        async def grant_access(self, database_id, target_user_id, access_level):
            self.calls.append((database_id, target_user_id, access_level))

    class FakeAuditService:
        async def record_event(self, **kwargs):
            return kwargs

    set_request_context(RequestContext(user_id=7, org_id=11, workspace_id=13, role="admin"))

    service = DatabaseService(
        FakeDbRepo(),
        audit_service=FakeAuditService(),
        grant_service=FakeGrantService(),
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("services.database_service.validate_database_connection", lambda **kwargs: None)
        mp.setattr("services.database_service.encrypt_password", lambda value: f"enc:{value}")
        db = await service.add_database(
            user_id=7,
            data=types.SimpleNamespace(
                host="localhost",
                port=5432,
                db_user="postgres",
                db_password="pw",
                db_name="appdb",
            ),
        )

    assert db.id == 99
    assert service.grant_service.calls == [(99, 7, DatabaseAccessLevel.MANAGE)]


@pytest.mark.asyncio(loop_scope="function")
async def test_mcp_denied_request_uses_governance_path(monkeypatch):
    class FakeTextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

    class FakeFastApiServer:
        def __init__(self, name: str):
            self.name = name
            self.app = object()

        def tool(self):
            def decorator(func):
                return func

            return decorator

    fake_mcp = types.ModuleType("mcp")
    fake_mcp_server = types.ModuleType("mcp.server")
    fake_mcp_server_fastapi = types.ModuleType("mcp.server.fastapi")
    fake_mcp_server_fastapi.FastApiServer = FakeFastApiServer
    fake_mcp_types = types.ModuleType("mcp.types")
    fake_mcp_types.Tool = object
    fake_mcp_types.TextContent = FakeTextContent

    fake_utils_agent = types.ModuleType("utils.agent")

    class FakeDatabaseAgent:
        pass

    fake_utils_agent.DatabaseAgent = FakeDatabaseAgent

    fake_ai_service = types.ModuleType("services.ai_service")

    class FakeAIService:
        @staticmethod
        def get_provider(provider_type: str, model_name=None):
            return object()

    fake_ai_service.AIService = FakeAIService

    monkeypatch.setitem(sys.modules, "mcp", fake_mcp)
    monkeypatch.setitem(sys.modules, "mcp.server", fake_mcp_server)
    monkeypatch.setitem(sys.modules, "mcp.server.fastapi", fake_mcp_server_fastapi)
    monkeypatch.setitem(sys.modules, "mcp.types", fake_mcp_types)
    monkeypatch.setitem(sys.modules, "utils.agent", fake_utils_agent)
    monkeypatch.setitem(sys.modules, "services.ai_service", fake_ai_service)
    sys.modules.pop("mcp_server", None)

    mcp_server = importlib.import_module("mcp_server")

    class FakeAgent:
        def __init__(self):
            self.tools = types.SimpleNamespace(user_db=types.SimpleNamespace(id=21, user_id=34))

        async def process_request(self, prompt: str):
            return {"sql": "SELECT * FROM secrets", "explanation": "test"}

    class FakeGovernanceService:
        def __init__(self):
            self.calls = []

        async def execute_governed_query(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "denied", "error": "Policy Denied: blocked table"}

    fake_agent = FakeAgent()
    fake_gov = FakeGovernanceService()

    response = await mcp_server.ask_database("show me secrets", None, fake_agent, fake_gov)

    assert len(fake_gov.calls) == 1
    assert fake_gov.calls[0]["db_id"] == 21
    assert fake_gov.calls[0]["user_id"] == 34
    assert fake_gov.calls[0]["sql"] == "SELECT * FROM secrets"
    assert response[0].type == "text"
    assert "Policy Denied" in response[0].text
