from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.approval_model import ApprovalRequest, ApprovalStatus
from typing import List, Optional

class ApprovalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: ApprovalRequest) -> ApprovalRequest:
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def get_by_id(self, request_id: int) -> Optional[ApprovalRequest]:
        return await self.session.get(ApprovalRequest, request_id)

    async def list_pending(self, workspace_id: int) -> List[ApprovalRequest]:
        result = await self.session.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.workspace_id == workspace_id,
                ApprovalRequest.status == ApprovalStatus.PENDING
            )
        )
        return result.scalars().all()

    async def update(self, request: ApprovalRequest) -> ApprovalRequest:
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request
