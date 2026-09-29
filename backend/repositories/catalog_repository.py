from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from models.catalog_model import CatalogEntry, ColumnAnnotation, BusinessTerm, MetricDefinition, CatalogStatus, MetricStatus
from typing import List, Optional

class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, entry_id: int, workspace_id: int) -> Optional[CatalogEntry]:
        result = await self.session.execute(
            select(CatalogEntry)
            .where(CatalogEntry.id == entry_id)
            .where(CatalogEntry.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_table(self, workspace_id: int, db_id: int, table_name: str) -> Optional[CatalogEntry]:
        result = await self.session.execute(
            select(CatalogEntry)
            .where(CatalogEntry.workspace_id == workspace_id, CatalogEntry.db_id == db_id, CatalogEntry.table_name == table_name)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: int, published_only=True, search=None) -> List[CatalogEntry]:
        query = select(CatalogEntry).where(CatalogEntry.workspace_id == workspace_id)
        if published_only:
            query = query.where(CatalogEntry.status == CatalogStatus.PUBLISHED)
        
        if search:
            query = query.where(CatalogEntry.table_name.ilike(f"%{search}%"))
            
        result = await self.session.execute(query.order_by(CatalogEntry.table_name))
        return result.scalars().all()

    async def create(self, entry: CatalogEntry) -> CatalogEntry:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def update(self, entry: CatalogEntry) -> CatalogEntry:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def add_column_annotation(self, annotation: ColumnAnnotation) -> ColumnAnnotation:
        self.session.add(annotation)
        await self.session.commit()
        await self.session.refresh(annotation)
        return annotation

class BusinessTermRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, term_id: int, workspace_id: int) -> Optional[BusinessTerm]:
        result = await self.session.execute(
            select(BusinessTerm)
            .where(BusinessTerm.id == term_id)
            .where(BusinessTerm.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: int, search=None) -> List[BusinessTerm]:
        query = select(BusinessTerm).where(BusinessTerm.workspace_id == workspace_id)
        if search:
            from sqlalchemy import or_
            query = query.where(or_(
                BusinessTerm.term.ilike(f"%{search}%"),
                BusinessTerm.definition.ilike(f"%{search}%")
            ))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, term: BusinessTerm) -> BusinessTerm:
        self.session.add(term)
        await self.session.commit()
        await self.session.refresh(term)
        return term

    async def find_by_term(self, workspace_id: int, term_name: str) -> Optional[BusinessTerm]:
        result = await self.session.execute(
            select(BusinessTerm).where(BusinessTerm.workspace_id == workspace_id, BusinessTerm.term == term_name)
        )
        return result.scalar_one_or_none()

class MetricDefinitionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_workspace(self, workspace_id: int, certified_only=True, search=None) -> List[MetricDefinition]:
        query = select(MetricDefinition).where(MetricDefinition.workspace_id == workspace_id)
        if certified_only:
            query = query.where(MetricDefinition.status == MetricStatus.CERTIFIED)
        
        if search:
            query = query.where(MetricDefinition.name.ilike(f"%{search}%"))
            
        result = await self.session.execute(query.order_by(MetricDefinition.name))
        return result.scalars().all()

    async def create(self, metric: MetricDefinition) -> MetricDefinition:
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric

    async def get_by_id(self, metric_id: int, workspace_id: int) -> Optional[MetricDefinition]:
        result = await self.session.execute(
            select(MetricDefinition)
            .where(MetricDefinition.id == metric_id)
            .where(MetricDefinition.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def update(self, metric: MetricDefinition) -> MetricDefinition:
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric

    async def delete(self, metric: MetricDefinition) -> None:
        await self.session.delete(metric)
        await self.session.commit()
