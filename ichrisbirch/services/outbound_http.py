"""The one way this app fetches a page from a third party.

Every caller that reaches a site outside this deployment goes through
`get_page`, so a timeout, a redirect policy or a fingerprint is decided once.

The request carries a real browser's TLS and HTTP/2 fingerprint. Sites behind
bot protection — Medium and its publications, most of the articles a person
saves — answer a plain HTTP client with 403 whatever user agent it claims,
because the refusal is decided on the handshake rather than the headers.

Requests to this app's own API are a different concern and do not belong here:
`ichrisbirch/api/client/` covers those. So does OIDC discovery in
`api/oidc_auth.py`, which talks to the identity provider with its own user agent
and its own caller-supplied timeout.
"""

from dataclasses import dataclass

from curl_cffi import requests as curl_requests
from curl_cffi.requests.exceptions import RequestException

# Long, because the callers are fetching arbitrary pages a person asked to save
# and a slow site is a normal outcome rather than a fault. A saved link can be a
# PDF of dozens of pages, which a slow host takes well over thirty seconds to send.
DEFAULT_TIMEOUT = 60.0

# curl_cffi's alias for the newest Chrome fingerprint it ships, so a dependency
# upgrade moves the fingerprint forward with the browser it imitates.
BROWSER_FINGERPRINT = 'chrome'


class PageFetchError(Exception):
    """The page could not be requested: DNS, TLS, the connection or the timeout failed."""

    def __init__(self, url: str, reason: str):
        super().__init__(f'could not fetch {url}: {reason}')
        self.url = url
        self.reason = reason


class PageStatusError(Exception):
    """The site answered, with a status that is not success."""

    def __init__(self, url: str, status_code: int):
        super().__init__(f'{url} answered {status_code}')
        self.url = url
        self.status_code = status_code


@dataclass(frozen=True)
class FetchedPage:
    """A response reduced to what callers read, so no caller depends on the HTTP library."""

    requested_url: str
    url: str
    status_code: int
    content: bytes

    def raise_for_status(self) -> 'FetchedPage':
        """Return the page when it succeeded, so a caller can chain it onto `get_page`."""
        if not 200 <= self.status_code < 300:
            raise PageStatusError(self.url, self.status_code)
        return self


def get_page(url: str, timeout: float = DEFAULT_TIMEOUT) -> FetchedPage:
    """Fetch a third-party page as a browser would, following redirects.

    The page is returned whatever its status: a caller that wants a non-2xx to be
    an error calls `.raise_for_status()`, and one that inspects the status still
    can. Only a request that never got an answer raises here.
    """
    try:
        response = curl_requests.get(url, impersonate=BROWSER_FINGERPRINT, timeout=timeout, allow_redirects=True)
    except RequestException as e:
        raise PageFetchError(url, str(e)) from e
    return FetchedPage(requested_url=url, url=str(response.url), status_code=response.status_code, content=response.content)
