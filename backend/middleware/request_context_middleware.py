import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.request_context import get_request_context, set_request_context, RequestContext

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Initialize context for this request
        context = RequestContext(request_id=request_id)
        set_request_context(context)
        
        response = await call_next(request)
        
        # Propagate Request ID back in response
        response.headers["X-Request-ID"] = request_id
        return response
