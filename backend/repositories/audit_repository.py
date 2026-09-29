import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, desc

from models.audit_model import AuditEvent

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _calculate_hash(self, event: AuditEvent) -> str:
        """
        Calculates SHA-256 hash of the event data and its previous_hash.
        The hash covers all immutable fields to make tampering detectable.
        """
        payload = {
            "event_type": event.event_type,
            "user_id": event.user_id,
            "org_id": event.org_id,
            "workspace_id": event.workspace_id,
            "request_id": event.request_id,
            "details": event.details,
            "previous_hash": event.previous_hash,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    async def create(self, event: AuditEvent) -> AuditEvent:
        """
        Appends an audit event, maintaining the tamper-evident hash chain.

        Race-condition note: two concurrent writes for the same workspace could both
        read the same last_event and set the same previous_hash, breaking the chain.
        The database-level fix is a UNIQUE constraint or advisory lock on the workspace_id.
        As a best-effort application-level mitigation we use SELECT FOR UPDATE via the
        with_for_update() hint when the DB supports it (PostgreSQL does).
        The chain remains verifiable; a broken link would be detected by verify_chain().
        """
        # Use FOR UPDATE to serialise concurrent chain writes for the same workspace.
        # If workspace_id is None (system events) we skip the chain.
        if event.workspace_id is not None:
            query = (
                select(AuditEvent)
                .where(AuditEvent.workspace_id == event.workspace_id)
                .order_by(desc(AuditEvent.id))
                .limit(1)
                .with_for_update()
            )
            result = await self.session.execute(query)
            last_event = result.scalar_one_or_none()
            event.previous_hash = last_event.hash if last_event else "GENESIS"
        else:
            event.previous_hash = "GENESIS"

        # Set timestamp with timezone if not already set
        if not event.created_at:
            event.created_at = datetime.now(timezone.utc)

        # Calculate hash
        event.hash = self._calculate_hash(event)

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def verify_chain(self, workspace_id: int) -> bool:
        """
        Verifies the integrity of the audit chain for a workspace.
        Returns True if the chain is intact, False if any tampering is detected.
        """
        query = (
            select(AuditEvent)
            .where(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.id.asc())
        )

        result = await self.session.execute(query)
        events = result.scalars().all()

        expected_previous_hash = "GENESIS"
        for event in events:
            if event.previous_hash != expected_previous_hash:
                logger.warning(
                    "Audit chain broken at event %d: expected prev_hash %s, got %s",
                    event.id, expected_previous_hash, event.previous_hash
                )
                return False

            recalculated = self._calculate_hash(event)
            if event.hash != recalculated:
                logger.warning(
                    "Audit event %d hash mismatch: stored %s, recalculated %s",
                    event.id, event.hash, recalculated
                )
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
        category: Optional[str] = None,
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
                "APPROVAL_DENIED", "DATA_EXPORTED", "CONNECTOR_HEALTH_CHECK",
            ]
            query = query.where(AuditEvent.event_type.in_(governance_events))

        if category:
            category_map = {
                "access": ["LOGIN_SUCCESS", "LOGIN_FAILURE", "WORKSPACE_SWITCHED"],
                "governance": ["EXECUTION_DENIED", "APPROVAL_REQUESTED", "APPROVAL_GRANTED", "APPROVAL_DENIED"],
                "data": ["DATA_EXPORTED", "SQL_EXECUTED", "SQL_GENERATED"],
                "config": ["DATABASE_ADDED", "MCP_KEY_ROTATED", "CONNECTOR_HEALTH_CHECK"],
            }
            if category in category_map:
                query = query.where(AuditEvent.event_type.in_(category_map[category]))

        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.session.execute(count_query)
        total_count = total_count_result.scalar() or 0

        # Paginate and order by newest first
        query = query.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total_count
