from contextvars import ContextVar
from typing import Optional
from pydantic import BaseModel

class RequestContext(BaseModel):
    request_id: Optional[str] = None
    user_id: Optional[int] = None
    org_id: Optional[int] = None
    workspace_id: Optional[int] = None
    membership_id: Optional[int] = None
    role: Optional[str] = None

_request_context_var: ContextVar[RequestContext] = ContextVar(
    "request_context", default=RequestContext()
)

def get_request_context() -> RequestContext:
    return _request_context_var.get()

def set_request_context(context: RequestContext):
    _request_context_var.set(context)
