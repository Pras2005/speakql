from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from typing import List, Dict, Any, Optional
from auth.auth_guards import require_analyst, require_compliance
from repositories.catalog_repository import CatalogRepository, BusinessTermRepository, MetricDefinitionRepository
from services.catalog_service import CatalogService
from schemas.catalog_schemas import CatalogEntryResponse, PublishTableRequest, BusinessTermCreate, BusinessTermResponse, MetricDefinitionCreate, MetricDefinitionUpdate, MetricDefinitionResponse

from repositories.audit_repository import AuditRepository
from services.audit_service import AuditService

router = APIRouter()

async def get_catalog_service(session: AsyncSession = Depends(get_session)):
    catalog_repo = CatalogRepository(session)
    glossary_repo = BusinessTermRepository(session)
    metric_repo = MetricDefinitionRepository(session)
    
    audit_repo = AuditRepository(session)
    audit_service = AuditService(audit_repo)
    
    return CatalogService(catalog_repo, glossary_repo, metric_repo, audit_service)

@router.get("", response_model=List[CatalogEntryResponse])
async def list_catalog(
    published_only: bool = True,
    search: Optional[str] = None,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_analyst)
):
    return await service.list_catalog(published_only=published_only, search=search)

@router.post("/publish", response_model=CatalogEntryResponse)
async def publish_table(
    request: PublishTableRequest,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_compliance)
):
    return await service.publish_table(request.db_id, request.table_name, request.description)

@router.post("/glossary", response_model=BusinessTermResponse)
async def create_glossary_term(
    request: BusinessTermCreate,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_compliance)
):
    return await service.create_business_term(
        request.term, request.definition, request.maps_to_table, request.maps_to_column
    )

@router.get("/glossary", response_model=List[BusinessTermResponse])
async def list_glossary(
    search: Optional[str] = None,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_analyst)
):
    workspace_id = token_data.get("workspace_id")
    return await service.glossary_repo.list_by_workspace(workspace_id, search=search)

@router.post("/metrics", response_model=MetricDefinitionResponse)
async def create_metric(
    request: MetricDefinitionCreate,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_compliance)
):
    return await service.create_metric(request.name, request.sql_expression, request.description)

@router.patch("/metrics/{metric_id}", response_model=MetricDefinitionResponse)
async def update_metric(
    metric_id: int,
    request: MetricDefinitionUpdate,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_compliance)
):
    updated = await service.update_metric(metric_id, request.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Metric not found")
    return updated

@router.delete("/metrics/{metric_id}")
async def delete_metric(
    metric_id: int,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_compliance)
):
    success = await service.delete_metric(metric_id)
    if not success:
        raise HTTPException(status_code=404, detail="Metric not found")
    return {"status": "deleted"}

@router.get("/metrics", response_model=List[MetricDefinitionResponse])
async def list_metrics(
    certified_only: bool = True,
    search: Optional[str] = None,
    service: CatalogService = Depends(get_catalog_service),
    token_data: dict = Depends(require_analyst)
):
    workspace_id = token_data.get("workspace_id")
    return await service.metric_repo.list_by_workspace(workspace_id, certified_only=certified_only, search=search)
