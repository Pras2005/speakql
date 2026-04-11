from sqlalchemy.ext.asyncio import AsyncSession
from models.audit_model import AuditEvent

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: AuditEvent) -> AuditEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
