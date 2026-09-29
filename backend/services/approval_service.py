from repositories.approval_repository import ApprovalRepository
from models.approval_model import ApprovalRequest, ApprovalStatus
from typing import List, Optional

class ApprovalService:
    def __init__(self, approval_repo: ApprovalRepository):
        self.approval_repo = approval_repo

    async def request_approval(
        self,
        workspace_id: int,
        requester_id: int,
        db_id: int,
        sql: str,
        risk_score: float,
        prompt: Optional[str] = None
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            workspace_id=workspace_id,
            requester_id=requester_id,
            db_id=db_id,
            sql_query=sql,
            risk_score=risk_score,
            original_prompt=prompt,
            status=ApprovalStatus.PENDING
        )
        return await self.approval_repo.create(request)

    async def get_pending_requests(self, workspace_id: int) -> List[ApprovalRequest]:
        return await self.approval_repo.list_pending(workspace_id)

    async def approve_request(self, request_id: int, workspace_id: int, approver_id: int) -> Optional[ApprovalRequest]:
        request = await self.approval_repo.get_by_id(request_id)
        if not request or request.workspace_id != workspace_id:
            return None
        
        request.status = ApprovalStatus.APPROVED
        request.approver_id = approver_id
        return await self.approval_repo.update(request)

    async def deny_request(self, request_id: int, workspace_id: int, approver_id: int, reason: str) -> Optional[ApprovalRequest]:
        request = await self.approval_repo.get_by_id(request_id)
        if not request or request.workspace_id != workspace_id:
            return None
        
        request.status = ApprovalStatus.DENIED
        request.approver_id = approver_id
        request.denial_reason = reason
        return await self.approval_repo.update(request)
