from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from repositories.database_repository import DatabaseRepository
from repositories.database_grant_repository import DatabaseGrantRepository
from repositories.audit_repository import AuditRepository
from services.database_service import DatabaseService
from services.audit_service import AuditService
from services.grant_service import GrantService
from repositories.catalog_repository import CatalogRepository, BusinessTermRepository, MetricDefinitionRepository
from services.catalog_service import CatalogService
from schemas.db_schemas import UserDatabaseCreate, UserDatabaseUpdate, UserDatabaseRead
from schemas.grant_schemas import DatabaseGrantCreate, DatabaseGrantRead, DatabaseGrantUpdate
from schemas.query_schemas import QueryHistoryRead
from auth.auth_bearer import JWTBearer
from typing import List
from models.tenant_model import DatabaseAccessLevel

router = APIRouter()

async def get_catalog_service(session: AsyncSession = Depends(get_session)):
    catalog_repo = CatalogRepository(session)
    glossary_repo = BusinessTermRepository(session)
    metric_repo = MetricDefinitionRepository(session)
    return CatalogService(catalog_repo, glossary_repo, metric_repo)

async def get_database_service(
    session: AsyncSession = Depends(get_session),
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    db_repo = DatabaseRepository(session)
    grant_repo = DatabaseGrantRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    grant_service = GrantService(grant_repo, db_repo, audit_service)
    return DatabaseService(db_repo, audit_service, catalog_service, grant_service)

async def get_grant_service(session: AsyncSession = Depends(get_session)):
    db_repo = DatabaseRepository(session)
    grant_repo = DatabaseGrantRepository(session)
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    return GrantService(grant_repo, db_repo, audit_service)

from auth.auth_guards import require_admin

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_db(
    db_data: UserDatabaseCreate,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_admin)
):
    user_id = int(token_data["sub"])
    try:
        db = await db_service.add_database(user_id, db_data)
        return {"msg": "Database added successfully", "db_id": db.id, "mcp_api_key": db.mcp_api_key}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("", response_model=List[UserDatabaseRead])
async def get_dbs(
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(JWTBearer(require_workspace=True))
):
    user_id = int(token_data["sub"])
    dbs = await db_service.get_databases(user_id)
    results = []
    for db in dbs:
        access_level = None
        if db_service.grant_service:
            access_level = await db_service.grant_service.get_effective_access_level(db.id, user_id)
        results.append(
            UserDatabaseRead.model_validate(
                db,
                update={
                    "name": db.db_name,
                    "access_level": access_level,
                    "connection_status": db.last_health_status or "unknown",
                    "workspace_id": db.workspace_id,
                },
            )
        )
    return results

@router.put("/{db_id}")
async def update_db(
    db_id: int,
    updates: UserDatabaseUpdate,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_admin)
):
    user_id = int(token_data["sub"])
    updated = await db_service.update_database(db_id, user_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"msg": "Database updated", "db_id": updated.id}

@router.delete("/{db_id}")
async def delete_db(
    db_id: int,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_admin)
):
    user_id = int(token_data["sub"])
    success = await db_service.delete_database(db_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"msg": "Database deleted successfully"}

@router.post("/{db_id}/rotate-mcp-key")
async def rotate_key(
    db_id: int,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_admin)
):
    user_id = int(token_data["sub"])
    new_key = await db_service.rotate_mcp_key(db_id, user_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"mcp_api_key": new_key}

@router.post("/{db_id}/refresh-catalog")
async def refresh_catalog(
    db_id: int,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(require_admin)
):
    user_id = int(token_data["sub"])
    can_manage = await db_service.has_database_access(db_id, user_id, DatabaseAccessLevel.MANAGE)
    if not can_manage:
        raise HTTPException(status_code=403, detail="Forbidden: manage grant required")
    await db_service.refresh_catalog(db_id)
    return {"msg": "Catalog refresh triggered"}

@router.get("/{db_id}/query-history", response_model=List[QueryHistoryRead])
async def get_query_history(
    db_id: int,
    db_service: DatabaseService = Depends(get_database_service),
    token_data: dict = Depends(JWTBearer(require_workspace=True))
):
    user_id = int(token_data["sub"])
    
    dbs = await db_service.get_databases(user_id)
    if not any(db.id == db_id for db in dbs):
        raise HTTPException(status_code=403, detail="Forbidden: Database not accessible")

    query_history = await db_service.get_query_history(db_id)
    return [
        QueryHistoryRead.model_validate(qh, update={
            "db_id": qh.user_database_id,
            "prompt": qh.original_prompt,
            "raw_sql": qh.executed_sql or qh.generated_sql,
            "status": "success" if qh.success else "error",
            "error": qh.error_message,
            "timestamp": qh.executed_at
        }) 
        for qh in query_history
    ]

@router.get("/{db_id}/grants", response_model=List[DatabaseGrantRead])
async def list_database_grants(
    db_id: int,
    grant_service: GrantService = Depends(get_grant_service),
    token_data: dict = Depends(require_admin),
):
    try:
        grants = await grant_service.list_grants(db_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [DatabaseGrantRead.model_validate(grant) for grant in grants]

@router.post("/{db_id}/grants", response_model=DatabaseGrantRead, status_code=status.HTTP_201_CREATED)
async def create_database_grant(
    db_id: int,
    payload: DatabaseGrantCreate,
    grant_service: GrantService = Depends(get_grant_service),
    token_data: dict = Depends(require_admin),
):
    try:
        grant = await grant_service.grant_access(db_id, payload.user_id, payload.access_level)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return DatabaseGrantRead.model_validate(grant)

@router.patch("/{db_id}/grants/{user_id}", response_model=DatabaseGrantRead)
async def update_database_grant(
    db_id: int,
    user_id: int,
    payload: DatabaseGrantUpdate,
    grant_service: GrantService = Depends(get_grant_service),
    token_data: dict = Depends(require_admin),
):
    try:
        grant = await grant_service.grant_access(db_id, user_id, payload.access_level)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return DatabaseGrantRead.model_validate(grant)

@router.delete("/{db_id}/grants/{user_id}")
async def delete_database_grant(
    db_id: int,
    user_id: int,
    grant_service: GrantService = Depends(get_grant_service),
    token_data: dict = Depends(require_admin),
):
    try:
        success = await grant_service.revoke_access(db_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not success:
        raise HTTPException(status_code=404, detail="Grant not found")
    return {"msg": "Database grant revoked"}
