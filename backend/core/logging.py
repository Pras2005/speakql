import logging
import sys
from core.request_context import get_request_context
from core.config import settings

class RequestContextFilter(logging.Filter):
    """
    Injection filter for RequestContext fields into log records.
    """
    def filter(self, record):
        context = get_request_context()
        record.request_id = context.request_id or "-"
        record.user_id = context.user_id or "-"
        record.org_id = context.org_id or "-"
        record.workspace_id = context.workspace_id or "-"
        return True

def setup_logging():
    # Base configuration
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "[req_id=%(request_id)s] [user=%(user_id)s] [org=%(org_id)s] [ws=%(workspace_id)s] "
        "%(message)s"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(RequestContextFilter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(handler)
    
    # Suppress verbose third-party logs
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Export a helper to get a logger
def get_logger(name: str):
    return logging.getLogger(name)
