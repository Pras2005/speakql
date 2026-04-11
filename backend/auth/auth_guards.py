from fastapi import Depends, HTTPException, status
from auth.auth_bearer import JWTBearer
from core.request_context import get_request_context
from models.tenant_model import MembershipRole
from typing import List

class RoleChecker:
    def __init__(self, allowed_roles: List[MembershipRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: dict = Depends(JWTBearer(require_workspace=True))):
        role = token_data.get("role")
        if role not in [r.value for r in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role} does not have permission to perform this action."
            )
        return token_data

# Common guards
require_admin = RoleChecker([MembershipRole.ADMIN])
require_analyst = RoleChecker([MembershipRole.ADMIN, MembershipRole.ANALYST])
require_compliance = RoleChecker([MembershipRole.ADMIN, MembershipRole.COMPLIANCE_ADMIN])
