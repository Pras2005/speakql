import secrets
from repositories.database_repository import DatabaseRepository
from services.audit_service import AuditService
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from models.tenant_model import DatabaseAccessLevel
from core.request_context import get_request_context
from utils.db_connection import validate_database_connection
from utils.encryption import encrypt_password, decrypt_password
from schemas.db_schemas import UserDatabaseCreate, UserDatabaseUpdate
from typing import List, Optional, Any
from utils.postgres_tools import get_postgresql_tools
from services.grant_service import GrantService

class DatabaseService:
    def __init__(
        self,
        db_repo: DatabaseRepository,
        audit_service: AuditService,
        catalog_service: Optional[Any] = None,
        grant_service: Optional[GrantService] = None,
    ):
        self.db_repo = db_repo
        self.audit_service = audit_service
        self.catalog_service = catalog_service
        self.grant_service = grant_service

    async def add_database(self, user_id: int, data: UserDatabaseCreate) -> UserDatabase:
        context = get_request_context()
        validate_database_connection(
            host=data.host,
            port=data.port,
            db_user=data.db_user,
            db_password=data.db_password,
            db_name=data.db_name,
        )
        encrypted_pass = encrypt_password(data.db_password)
        user_db = UserDatabase(
            user_id=user_id,
            org_id=context.org_id,
            workspace_id=context.workspace_id,
            host=data.host,
            port=data.port,
            db_user=data.db_user,
            db_password_encrypted=encrypted_pass,
            db_name=data.db_name,
            mcp_api_key=secrets.token_urlsafe(32)
        )
        db = await self.db_repo.create(user_db)

        if self.grant_service:
            await self.grant_service.grant_access(
                database_id=db.id,
                target_user_id=user_id,
                access_level=DatabaseAccessLevel.MANAGE,
            )
        
        # Log audit event
        await self.audit_service.record_event(
            event_type="DATABASE_ADDED",
            user_id=user_id,
            details={"database_id": db.id, "db_name": db.db_name}
        )
        
        # Trigger catalog refresh
        if self.catalog_service:
            await self.refresh_catalog(db.id)
            
        return db

    async def refresh_catalog(self, db_id: int):
        """Discovers tables and populates draft catalog entries."""
        db = await self.db_repo.get_by_id(db_id)
        if not db or not self.catalog_service:
            return
            
        tools = get_postgresql_tools(db)
        tables = await tools.list_tables()
        await self.catalog_service.generate_draft_catalog(db_id, tables)

    async def get_databases(self, user_id: int) -> List[UserDatabase]:
        context = get_request_context()
        if not self.grant_service:
            return await self.db_repo.list_by_workspace(context.workspace_id)
        granted_ids = await self.grant_service.list_database_ids_for_user(user_id)
        return await self.db_repo.list_by_ids(context.workspace_id, granted_ids)

    async def has_database_access(
        self, db_id: int, user_id: int, required_level: DatabaseAccessLevel
    ) -> bool:
        context = get_request_context()
        db = await self.db_repo.get_by_id(db_id, workspace_id=context.workspace_id)
        if not db:
            return False
        if not self.grant_service:
            return True
        return await self.grant_service.has_access(db_id, user_id, required_level)

    async def update_database(self, db_id: int, user_id: int, updates: UserDatabaseUpdate) -> Optional[UserDatabase]:
        db = await self.db_repo.get_by_id(db_id)
        context = get_request_context()
        
        if not db or db.workspace_id != context.workspace_id:
            return None
        if not await self.has_database_access(db_id, user_id, DatabaseAccessLevel.MANAGE):
            return None

        update_data = updates.model_dump(exclude_unset=True)
        
        conn_params = ["host", "port", "db_user", "db_password", "db_name"]
        if any(p in update_data for p in conn_params):
            merged_config = {
                "host": update_data.get("host", db.host),
                "port": update_data.get("port", db.port),
                "db_user": update_data.get("db_user", db.db_user),
                "db_password": update_data.get("db_password", decrypt_password(db.db_password_encrypted)),
                "db_name": update_data.get("db_name", db.db_name),
            }
            validate_database_connection(**merged_config)

        for key, value in update_data.items():
            if key == "db_password":
                value = encrypt_password(value)
                setattr(db, "db_password_encrypted", value)
            elif hasattr(db, key):
                setattr(db, key, value)

        return await self.db_repo.update(db)

    async def delete_database(self, db_id: int, user_id: int) -> bool:
        db = await self.db_repo.get_by_id(db_id)
        context = get_request_context()
        if not db or db.workspace_id != context.workspace_id:
            return False
        if not await self.has_database_access(db_id, user_id, DatabaseAccessLevel.MANAGE):
            return False
        await self.db_repo.delete(db)
        return True

    async def rotate_mcp_key(self, db_id: int, user_id: int) -> Optional[str]:
        db = await self.db_repo.get_by_id(db_id)
        context = get_request_context()
        if not db or db.workspace_id != context.workspace_id:
            return None
        if not await self.has_database_access(db_id, user_id, DatabaseAccessLevel.MANAGE):
            return None
        db.mcp_api_key = secrets.token_urlsafe(32)
        await self.db_repo.update(db)
        
        await self.audit_service.record_event(
            event_type="MCP_KEY_ROTATED",
            user_id=user_id,
            details={"database_id": db.id}
        )
        return db.mcp_api_key

    async def log_query(
        self,
        db_id: int,
        user_id: int,
        event_type: str,
        prompt: Optional[str] = None,
        generated_sql: Optional[str] = None,
        executed_sql: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> QueryHistory:
        context = get_request_context()
        history = QueryHistory(
            user_database_id=db_id,
            org_id=context.org_id,
            workspace_id=context.workspace_id,
            event_type=event_type,
            original_prompt=prompt,
            generated_sql=generated_sql,
            executed_sql=executed_sql,
            success=success,
            error_message=error
        )
        qh = await self.db_repo.add_query_history(history)
        
        # Log to audit vault too
        audit_event_type = "SQL_GENERATED" if event_type == "generation" else "SQL_EXECUTED"
        if not success and error:
            # If denied by safety, policy or other reason
            err_lower = error.lower()
            if any(term in err_lower for term in ["safety", "permission", "policy denied", "blocked"]):
                audit_event_type = "EXECUTION_DENIED"

        await self.audit_service.record_event(
            event_type=audit_event_type,
            user_id=user_id,
            details={
                "database_id": db_id,
                "success": success,
                "error": error
            }
        )
        return qh

    async def get_query_history(self, db_id: int) -> List[QueryHistory]:
        db = await self.db_repo.get_by_id(db_id)
        context = get_request_context()
        if not db or db.workspace_id != context.workspace_id:
            return []
        return await self.db_repo.list_query_history(db_id)
