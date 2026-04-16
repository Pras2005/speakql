from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.policy_model import Policy
from typing import List, Optional

class PolicyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, policy_id: int) -> Optional[Policy]:
        return await self.session.get(Policy, policy_id)

    async def list_by_workspace(self, workspace_id: int) -> List[Policy]:
        result = await self.session.execute(
            select(Policy).where(
                Policy.workspace_id == workspace_id,
                Policy.active == True
            ).order_by(Policy.priority.desc())
        )
        return result.scalars().all()

    async def create(self, policy: Policy) -> Policy:
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def update(self, policy: Policy) -> Policy:
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def delete(self, policy: Policy):
        await self.session.delete(policy)
        await self.session.commit()
