"""Custom exceptions for the API client.

These exceptions are raised when API calls fail, allowing Flask routes
to distinguish between "no data" and "API error" scenarios.
"""


class APIClientError(Exception):
    """Base exception for all API client errors.

    Attributes:
        message: Human-readable error description
        status_code: HTTP status code if available (None for connection errors)
        response_text: Raw response body if available
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f'{self.message} (HTTP {self.status_code})'
        return self.message


class APIHTTPError(APIClientError):
    """HTTP error response from the API (4xx, 5xx status codes).

    Raised when the API returns an error status code.
    """

    pass


class APIConnectionError(APIClientError):
    """Network or connection error.

    Raised when the client cannot reach the API (DNS failure,
    connection refused, timeout, etc.).
    """

    pass


class APIParseError(APIClientError):
    """Failed to parse API response.

    Raised when the response cannot be parsed as expected
    (invalid JSON, schema mismatch, etc.).
    """

    pass
