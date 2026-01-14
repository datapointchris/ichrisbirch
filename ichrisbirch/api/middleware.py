import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class ResponseLoggerMiddleware(BaseHTTPMiddleware):
    """Logs all requests and responses from the API with request tracing."""

    async def dispatch(self, request: Request, call_next):
        """Process request with timing, logging, and request ID tracking."""
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)

        response.headers['X-Request-ID'] = request_id

        if request.method == 'GET' and request.url.path == '/health':
            structlog.contextvars.clear_contextvars()
            return response

        log_data = {
            'method': request.method,
            'path': request.url.path,
            'status': response.status_code,
            'duration_ms': process_time,
        }

        if response.status_code >= 500:
            logger.error('request_completed', **log_data)
        elif response.status_code >= 400:
            logger.warning('request_completed', **log_data)
        else:
            logger.info('request_completed', **log_data)

        structlog.contextvars.clear_contextvars()
        return response
