from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, desc
from models.audit_model import AuditEvent
from typing import List, Optional, Tuple
from datetime import datetime
import hashlib
import json

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _calculate_hash(self, event: AuditEvent) -> str:
        """
        Calculates SHA-256 hash of the event data and its previous_hash.
        """
        payload = {
            "event_type": event.event_type,
            "user_id": event.user_id,
            "org_id": event.org_id,
            "workspace_id": event.workspace_id,
            "request_id": event.request_id,
            "details": event.details,
            "previous_hash": event.previous_hash,
            "created_at": event.created_at.isoformat() if event.created_at else None
        }
        encoded = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    async def create(self, event: AuditEvent) -> AuditEvent:
        # 1. Find previous hash for this workspace
        query = select(AuditEvent).where(
            AuditEvent.workspace_id == event.workspace_id
        ).order_by(desc(AuditEvent.id)).limit(1)
        
        result = await self.session.execute(query)
        last_event = result.scalar_one_or_none()
        
        event.previous_hash = last_event.hash if last_event else "GENESIS"
        
        # 2. Set timestamp if not set
        if not event.created_at:
            event.created_at = datetime.utcnow()
            
        # 3. Calculate hash
        event.hash = self._calculate_hash(event)
        
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def verify_chain(self, workspace_id: int) -> bool:
        """
        Verifies the integrity of the audit chain for a workspace.
        """
        query = select(AuditEvent).where(
            AuditEvent.workspace_id == workspace_id
        ).order_by(AuditEvent.id.asc())
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        expected_previous_hash = "GENESIS"
        for event in events:
            if event.previous_hash != expected_previous_hash:
                return False
            
            if event.hash != self._calculate_hash(event):
                return False
                
            expected_previous_hash = event.hash
            
        return True

    async def list_by_workspace(
        self, 
        workspace_id: int, 
        skip: int = 0, 
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        governance_only: bool = False,
        category: Optional[str] = None
    ) -> Tuple[List[AuditEvent], int]:
        """
        Returns a list of audit events and the total count for pagination with rich filtering.
        """
        query = select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)
        
        if event_type:
            query = query.where(AuditEvent.event_type == event_type)
        if user_id:
            query = query.where(AuditEvent.user_id == user_id)
        if start_date:
            query = query.where(AuditEvent.created_at >= start_date)
        if end_date:
            query = query.where(AuditEvent.created_at <= end_date)
            
        if governance_only:
            governance_events = [
                "EXECUTION_DENIED", "APPROVAL_REQUESTED", "APPROVAL_GRANTED", 
                "APPROVAL_DENIED", "DATA_EXPORTED", "CONNECTOR_HEALTH_CHECK"
            ]
            query = query.where(AuditEvent.event_type.in_(governance_events))
            
        if category:
            category_map = {
                "access": ["LOGIN_SUCCESS", "LOGIN_FAILURE", "WORKSPACE_SWITCHED"],
                "governance": ["EXECUTION_DENIED", "APPROVAL_REQUESTED", "APPROVAL_GRANTED", "APPROVAL_DENIED"],
                "data": ["DATA_EXPORTED", "SQL_EXECUTED", "SQL_GENERATED"],
                "config": ["DATABASE_ADDED", "MCP_KEY_ROTATED", "CONNECTOR_HEALTH_CHECK"]
            }
            if category in category_map:
                query = query.where(AuditEvent.event_type.in_(category_map[category]))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.session.execute(count_query)
        total_count = total_count_result.scalar() or 0
        
        # Paginate and order by newest first
        query = query.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total_count
