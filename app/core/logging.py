import logging
import sys
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get() or "-"
        return True


def setup_logging():
    """Configure structured logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIdFilter())


def get_request_id() -> str:
    """Get current request ID"""
    return request_id_var.get()


def set_request_id(request_id: str = None):
    """Set request ID for current context"""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id
