from typing import List, Optional, Dict, Any
from models.catalog_model import CatalogEntry, ColumnAnnotation, BusinessTerm, MetricDefinition, CatalogStatus, MetricStatus
from repositories.catalog_repository import CatalogRepository, BusinessTermRepository, MetricDefinitionRepository
from core.request_context import get_request_context
from datetime import datetime, timezone

class CatalogService:
    def __init__(
        self, 
        catalog_repo: CatalogRepository, 
        glossary_repo: BusinessTermRepository,
        metric_repo: MetricDefinitionRepository,
        audit_service: Optional[Any] = None
    ):
        self.catalog_repo = catalog_repo
        self.glossary_repo = glossary_repo
        self.metric_repo = metric_repo
        self.audit_service = audit_service

    async def get_catalog_entry(self, entry_id: int) -> Optional[CatalogEntry]:
        context = get_request_context()
        return await self.catalog_repo.get_by_id(entry_id, context.workspace_id)

    async def list_catalog(self, published_only=True, search: Optional[str] = None) -> List[CatalogEntry]:
        context = get_request_context()
        return await self.catalog_repo.list_by_workspace(context.workspace_id, published_only=published_only, search=search)

    async def publish_table(self, db_id: int, table_name: str, description: str) -> CatalogEntry:
        context = get_request_context()
        entry = await self.catalog_repo.get_by_table(context.workspace_id, db_id, table_name)
        if entry:
            entry.description = description
            entry.status = CatalogStatus.PUBLISHED
            entry.updated_at = datetime.now(timezone.utc)
            res = await self.catalog_repo.update(entry)
        else:
            entry = CatalogEntry(
                workspace_id=context.workspace_id,
                db_id=db_id,
                table_name=table_name,
                description=description,
                status=CatalogStatus.PUBLISHED
            )
            res = await self.catalog_repo.create(entry)
        
        if self.audit_service:
            await self.audit_service.record_event(
                event_type="CATALOG_TABLE_PUBLISHED",
                user_id=context.user_id,
                details={"db_id": db_id, "table": table_name}
            )
        return res

    async def generate_draft_catalog(self, db_id: int, tables: List[str]):
        """Generates draft catalog entries for a list of tables."""
        context = get_request_context()
        for table in tables:
            existing = await self.catalog_repo.get_by_table(context.workspace_id, db_id, table)
            if not existing:
                entry = CatalogEntry(
                    workspace_id=context.workspace_id,
                    db_id=db_id,
                    table_name=table,
                    description=f"Auto-discovered table: {table}",
                    status=CatalogStatus.DRAFT
                )
                await self.catalog_repo.create(entry)
        
        if self.audit_service:
            await self.audit_service.record_event(
                event_type="CATALOG_DRAFT_GENERATED",
                user_id=context.user_id,
                details={"db_id": db_id, "table_count": len(tables)}
            )

    async def update_metric(self, metric_id: int, updates: Dict[str, Any]) -> Optional[MetricDefinition]:
        context = get_request_context()
        metric = await self.metric_repo.get_by_id(metric_id, context.workspace_id)
        if not metric:
            return None
        for key, value in updates.items():
            if hasattr(metric, key):
                setattr(metric, key, value)
        metric.updated_at = datetime.now(timezone.utc)
        updated = await self.metric_repo.update(metric)

        if self.audit_service:
            await self.audit_service.record_event(
                event_type="METRIC_UPDATED",
                user_id=context.user_id,
                details={"metric_id": metric_id, "name": metric.name}
            )
        return updated

    async def delete_metric(self, metric_id: int) -> bool:
        context = get_request_context()
        metric = await self.metric_repo.get_by_id(metric_id, context.workspace_id)
        if not metric:
            return False
        name = metric.name
        await self.metric_repo.delete(metric)

        if self.audit_service:
            await self.audit_service.record_event(
                event_type="METRIC_DELETED",
                user_id=context.user_id,
                details={"metric_id": metric_id, "name": name}
            )
        return True

    async def certify_metric(self, metric_id: int) -> Optional[MetricDefinition]:
        """Marks a metric as CERTIFIED."""
        return await self.update_metric(metric_id, {"status": MetricStatus.CERTIFIED})

    async def get_semantic_context(self) -> str:
        """Returns a string representation of glossary terms and certified metrics for LLM context."""
        context = get_request_context()
        workspace_id = context.workspace_id
        
        glossary = await self.glossary_repo.list_by_workspace(workspace_id)
        metrics = await self.metric_repo.list_by_workspace(workspace_id, certified_only=True)
        
        lines = []
        if glossary:
            lines.append("BUSINESS GLOSSARY:")
            for term in glossary:
                mapping = f" (maps to {term.maps_to_table}.{term.maps_to_column})" if term.maps_to_table else ""
                lines.append(f"- {term.term}: {term.definition}{mapping}")
        
        if metrics:
            lines.append("\nCERTIFIED METRICS:")
            for m in metrics:
                lines.append(f"- {m.name}: {m.sql_expression} ({m.description or ''})")
                
        return "\n".join(lines)

    async def create_business_term(self, term: str, definition: str, maps_to_table: Optional[str] = None, maps_to_column: Optional[str] = None) -> BusinessTerm:
        context = get_request_context()
        new_term = BusinessTerm(
            workspace_id=context.workspace_id,
            term=term,
            definition=definition,
            maps_to_table=maps_to_table,
            maps_to_column=maps_to_column
        )
        saved = await self.glossary_repo.create(new_term)
        if self.audit_service:
            await self.audit_service.record_event(
                event_type="GLOSSARY_TERM_CREATED",
                user_id=context.user_id,
                details={"term_id": saved.id, "term": saved.term}
            )
        return saved

    async def create_metric(self, name: str, expression: str, description: Optional[str] = None) -> MetricDefinition:
        context = get_request_context()
        metric = MetricDefinition(
            workspace_id=context.workspace_id,
            name=name,
            sql_expression=expression,
            description=description,
            status=MetricStatus.DRAFT
        )
        saved = await self.metric_repo.create(metric)
        if self.audit_service:
            await self.audit_service.record_event(
                event_type="METRIC_CREATED",
                user_id=context.user_id,
                details={"metric_id": saved.id, "name": saved.name}
            )
        return saved
