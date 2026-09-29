from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from models.report_model import Report, ReportRun
from typing import List, Optional

class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, report_id: int, workspace_id: int) -> Optional[Report]:
        result = await self.session.execute(
            select(Report)
            .where(Report.id == report_id)
            .where(Report.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: int, enabled_only=False) -> List[Report]:
        query = select(Report).where(Report.workspace_id == workspace_id)
        if enabled_only:
            query = query.where(Report.is_enabled == True)
        
        result = await self.session.execute(query.order_by(Report.name))
        return result.scalars().all()

    async def create(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def update(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def delete(self, report: Report):
        await self.session.delete(report)
        await self.session.commit()

class ReportRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, run_id: int, workspace_id: int) -> Optional[ReportRun]:
        result = await self.session.execute(
            select(ReportRun)
            .where(ReportRun.id == run_id)
            .where(ReportRun.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def create(self, run: ReportRun) -> ReportRun:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def list_by_report(self, report_id: int, workspace_id: int, limit=50) -> List[ReportRun]:
        result = await self.session.execute(
            select(ReportRun)
            .where(ReportRun.report_id == report_id)
            .where(ReportRun.workspace_id == workspace_id)
            .order_by(desc(ReportRun.executed_at))
            .limit(limit)
        )
        return result.scalars().all()
