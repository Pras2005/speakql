from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from models.workflow_model import SavedQuery, SavedQueryRun, QueryComment, SavedQueryStatus, SavedQueryVisibility
from typing import List, Optional

class SavedQueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, query_id: int, workspace_id: int) -> Optional[SavedQuery]:
        result = await self.session.execute(
            select(SavedQuery)
            .where(SavedQuery.id == query_id)
            .where(SavedQuery.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self, 
        workspace_id: int, 
        include_private=False, 
        user_id=None, 
        search=None,
        status: Optional[SavedQueryStatus] = None,
        visibility: Optional[SavedQueryVisibility] = None,
        owner_id: Optional[int] = None
    ) -> List[SavedQuery]:
        query = select(SavedQuery).where(SavedQuery.workspace_id == workspace_id)
        
        if not include_private:
            query = query.where(SavedQuery.visibility == SavedQueryVisibility.WORKSPACE_SHARED)
        elif user_id:
            # Show shared OR own private
            from sqlalchemy import or_
            query = query.where(or_(
                SavedQuery.visibility == SavedQueryVisibility.WORKSPACE_SHARED,
                SavedQuery.created_by == user_id
            ))

        if status:
            query = query.where(SavedQuery.status == status)
        
        if visibility:
            query = query.where(SavedQuery.visibility == visibility)
            
        if owner_id:
            query = query.where(SavedQuery.created_by == owner_id)
        
        if search:
            from sqlalchemy import or_
            query = query.where(or_(
                SavedQuery.name.ilike(f"%{search}%"),
                SavedQuery.description.ilike(f"%{search}%"),
                SavedQuery.tags.ilike(f"%{search}%")
            ))
            
        result = await self.session.execute(query.order_by(desc(SavedQuery.created_at)))
        return result.scalars().all()

    async def create(self, saved_query: SavedQuery) -> SavedQuery:
        self.session.add(saved_query)
        await self.session.commit()
        await self.session.refresh(saved_query)
        return saved_query

    async def update(self, saved_query: SavedQuery) -> SavedQuery:
        self.session.add(saved_query)
        await self.session.commit()
        await self.session.refresh(saved_query)
        return saved_query

    async def delete(self, saved_query: SavedQuery):
        await self.session.delete(saved_query)
        await self.session.commit()

    async def create_run(self, run: SavedQueryRun) -> SavedQueryRun:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def list_runs(self, query_id: int, workspace_id: int) -> List[SavedQueryRun]:
        result = await self.session.execute(
            select(SavedQueryRun)
            .where(SavedQueryRun.saved_query_id == query_id)
            .where(SavedQueryRun.workspace_id == workspace_id)
            .order_by(desc(SavedQueryRun.executed_at))
        )
        return result.scalars().all()

class QueryCommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, comment_id: int, workspace_id: int) -> Optional[QueryComment]:
        result = await self.session.execute(
            select(QueryComment)
            .where(QueryComment.id == comment_id)
            .where(QueryComment.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def create(self, comment: QueryComment) -> QueryComment:
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def list_by_query(self, query_id: int, workspace_id: int) -> List[QueryComment]:
        result = await self.session.execute(
            select(QueryComment)
            .where(QueryComment.saved_query_id == query_id)
            .where(QueryComment.workspace_id == workspace_id)
            .order_by(QueryComment.created_at)
        )
        return result.scalars().all()

    async def delete(self, comment: QueryComment):
        await self.session.delete(comment)
        await self.session.commit()

    async def update(self, comment: QueryComment) -> QueryComment:
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment
