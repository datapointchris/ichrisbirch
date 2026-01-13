import time
import uuid

import structlog
from flask import Flask
from flask import g
from flask import request

logger = structlog.get_logger()


class RequestLoggingMiddleware:
    """Custom request logging middleware for Flask app with request tracing."""

    def __init__(self, app: Flask | None = None):
        self.HEALTHCHECK_IPS = {'127.0.0.1', '172.17.0.1', '172.18.0.1'}
        self.STATIC_EXTENSIONS = {'.css', '.js', '.woff', '.woff2', '.ico', '.png', '.jpg', '.svg'}

        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)

    def before_request(self):
        """Set up request context with timing and request ID."""
        g.start_time = time.time()

        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        g.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)

    def after_request(self, response):
        """Log completed requests and add request ID to response."""
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id

        start_time = getattr(g, 'start_time', time.time())
        duration = round((time.time() - start_time) * 1000, 2)

        if self._is_healthcheck_request():
            return response

        if self._is_static_file():
            return response

        if response.status_code == 304:
            return response

        self._log_request(response, duration)
        return response

    def teardown_request(self, exception):
        """Clean up request context."""
        structlog.contextvars.clear_contextvars()

    def _is_healthcheck_request(self) -> bool:
        """Check if request is from healthcheck IP."""
        client_ip = request.environ.get('REMOTE_ADDR', '')
        return client_ip in self.HEALTHCHECK_IPS

    def _is_static_file(self) -> bool:
        """Check if request is for static files."""
        path = request.path.lower()
        return any(path.endswith(ext) for ext in self.STATIC_EXTENSIONS)

    def _log_request(self, response, duration: float):
        """Log the request with structured data."""
        status = response.status_code
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')

        log_data = {
            'client_ip': client_ip,
            'method': request.method,
            'path': request.path,
            'status': status,
            'duration_ms': duration,
        }

        if status >= 500:
            logger.error('request_completed', **log_data)
        elif status >= 400:
            logger.warning('request_completed', **log_data)
        else:
            logger.info('request_completed', **log_data)
