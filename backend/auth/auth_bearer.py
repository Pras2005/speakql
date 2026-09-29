from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_factory
from repositories.user_repository import UserRepository
from core.auth import decode_token
from core.request_context import get_request_context, set_request_context, RequestContext

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True, require_workspace: bool = False, verify_version: bool = False):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.require_workspace = require_workspace
        self.verify_version = verify_version

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            try:
                payload = decode_token(credentials.credentials)

                # Build a new RequestContext from the JWT payload.
                # We must NOT mutate the existing context object in-place because
                # ContextVar holds a reference to it — other coroutines may share it.
                existing = get_request_context()
                new_context = RequestContext(
                    request_id=existing.request_id,  # Preserve request_id set by middleware
                    user_id=int(payload["sub"]) if payload.get("sub") else None,
                    org_id=payload.get("org_id"),
                    workspace_id=payload.get("workspace_id"),
                    membership_id=payload.get("membership_id"),
                    role=payload.get("role"),
                )
                set_request_context(new_context)

                # Verify token version if requested (high-risk routes)
                if self.verify_version and payload.get("sub"):
                    async with async_session_factory() as session:
                        user_repo = UserRepository(session)
                        user = await user_repo.get_by_id(int(payload.get("sub")))
                        if not user or user.token_version != payload.get("token_version"):
                            raise HTTPException(status_code=401, detail="Token revoked or outdated")

                if self.require_workspace and not new_context.workspace_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Active workspace context required. Please select a workspace.",
                    )

                return payload
            except HTTPException:
                raise
            except (JWTError, ValueError):
                raise HTTPException(status_code=401, detail="Invalid or expired token")

        if self.auto_error:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        return None
