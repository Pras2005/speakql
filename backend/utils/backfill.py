import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from database import engine, async_session_factory
from models.user_model import User
from models.tenant_model import Organization, Workspace, Membership, MembershipRole
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from models.mcp_model import WorkspaceApiKey
from repositories.tenant_repository import TenantRepository
from services.tenant_service import TenantService
from repositories.api_key_repository import ApiKeyRepository

logger = logging.getLogger(__name__)

async def run_backfill():
    async with async_session_factory() as session:
        tenant_repo = TenantRepository(session)
        tenant_service = TenantService(tenant_repo)
        
        # 1. Identify users without memberships
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            memberships = await tenant_service.get_user_memberships(user.id)
            if not memberships:
                logger.info("Backfilling tenant context for user: %s", user.username)
                org, workspace = await tenant_service.setup_default_tenant(user.id)
                
                # 2. Backfill existing databases for this user
                db_result = await session.execute(
                    select(UserDatabase).where(UserDatabase.user_id == user.id)
                )
                dbs = db_result.scalars().all()
                for db in dbs:
                    if not db.org_id or not db.workspace_id:
                        logger.info("  Updating database: %s", db.db_name)
                        db.org_id = org.id
                        db.workspace_id = workspace.id
                        session.add(db)
                        
                        # 3. Backfill query history for this database
                        qh_result = await session.execute(
                            select(QueryHistory).where(QueryHistory.user_database_id == db.id)
                        )
                        qhs = qh_result.scalars().all()
                        for qh in qhs:
                            if not qh.org_id or not qh.workspace_id:
                                qh.org_id = org.id
                                qh.workspace_id = workspace.id
                                session.add(qh)

                    # 4. Migrate legacy MCP Keys to Workspace Keys
                    if db.mcp_api_key:
                        logger.info("  Migrating MCP key for DB: %s", db.db_name)
                        hashed = ApiKeyRepository._hash_key(db.mcp_api_key)
                        key_exists_result = await session.execute(
                            select(WorkspaceApiKey).where(WorkspaceApiKey.hashed_key == hashed)
                        )
                        if not key_exists_result.scalar_one_or_none():
                            new_key = WorkspaceApiKey(
                                org_id=db.org_id,
                                workspace_id=db.workspace_id,
                                user_id=db.user_id,
                                name=f"Migrated Key - {db.db_name}",
                                key_prefix=db.mcp_api_key[:8],
                                hashed_key=hashed,
                                default_db_id=db.id,
                                role=MembershipRole.ANALYST
                            )
                            session.add(new_key)
        
        await session.commit()
        logger.info("Backfill completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_backfill())
