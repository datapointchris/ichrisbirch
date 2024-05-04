import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger('response_logger')


class ResponseLoggerMiddleware(BaseHTTPMiddleware):
    """Logs all requests and responses from the API."""

    async def dispatch(self, request: Request, call_next):
        """Returns the request path, processing time, and response status code for every API call."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(
            f'{request.method} {request.url.path} completed in {process_time:.6f} status code {response.status_code}'
        )
        return response
