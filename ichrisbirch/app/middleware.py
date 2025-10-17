import logging
import time

from flask import Flask
from flask import g
from flask import request

logger = logging.getLogger('app')


class RequestLoggingMiddleware:
    """Custom request logging middleware for Flask app."""

    def __init__(self, app: Flask | None = None):
        # Configuration
        self.HEALTHCHECK_IPS = {'127.0.0.1', '172.17.0.1', '172.18.0.1'}
        self.STATIC_EXTENSIONS = {'.css', '.js', '.woff', '.woff2', '.ico', '.png', '.jpg', '.svg'}

        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the middleware with Flask app."""
        # Register hooks
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Record request start time."""
        g.start_time = time.time()

    def after_request(self, response):
        """Log completed requests with filtering."""
        # Safely get start_time with a fallback
        start_time = getattr(g, 'start_time', time.time())
        duration = round((time.time() - start_time) * 1000, 2)

        # Skip healthcheck requests
        if self._is_healthcheck_request():
            return response

        # Skip static files
        if self._is_static_file():
            return response

        # Skip 304 status codes (like existing filter)
        if response.status_code == 304:
            return response

        # Log the request
        self.request_received(response, duration)

        return response

    def _is_healthcheck_request(self) -> bool:
        """Check if request is from healthcheck IP."""
        client_ip = request.environ.get('REMOTE_ADDR', '')
        return client_ip in self.HEALTHCHECK_IPS

    def _is_static_file(self) -> bool:
        """Check if request is for static files."""
        path = request.path.lower()
        return any(path.endswith(ext) for ext in self.STATIC_EXTENSIONS)

    def request_received(self, response, duration: float):
        """Log the request with consistent format."""
        method = request.method
        path = request.path
        status = response.status_code
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        # user_agent = request.headers.get('User-Agent', '')[:100]  # Truncate UA

        # Log level based on status code
        if status >= 500:
            log_level = logging.ERROR
        elif status >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        logger.log(log_level, f'{client_ip} {method} {path} {status} {duration}ms')
