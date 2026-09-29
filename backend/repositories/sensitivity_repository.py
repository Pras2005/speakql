from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.sensitivity_model import SensitivityRule
from typing import List, Optional

class SensitivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, rule_id: int) -> Optional[SensitivityRule]:
        return await self.session.get(SensitivityRule, rule_id)

    async def list_by_workspace(self, workspace_id: int) -> List[SensitivityRule]:
        result = await self.session.execute(
            select(SensitivityRule).where(
                SensitivityRule.workspace_id == workspace_id,
                SensitivityRule.active == True
            ).order_by(SensitivityRule.priority.desc())
        )
        return result.scalars().all()

    async def get_rules_for_table(self, workspace_id: int, table_name: str) -> List[SensitivityRule]:
        result = await self.session.execute(
            select(SensitivityRule).where(
                SensitivityRule.workspace_id == workspace_id,
                SensitivityRule.table_name == table_name,
                SensitivityRule.active == True
            ).order_by(SensitivityRule.priority.desc())
        )
        return result.scalars().all()

    async def create(self, rule: SensitivityRule) -> SensitivityRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def update(self, rule: SensitivityRule) -> SensitivityRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, rule: SensitivityRule):
        await self.session.delete(rule)
        await self.session.commit()
