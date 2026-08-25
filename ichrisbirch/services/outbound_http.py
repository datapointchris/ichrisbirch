"""The one way this app fetches a page from a third party.

Every caller that reaches a site outside this deployment goes through
`get_page`. Five call sites previously repeated the same three arguments by
hand, and four of them left the timeout at httpx's default while the fifth set
thirty seconds — so the same fetch behaved differently depending on which
endpoint made it.

Requests to this app's own API are a different concern and do not belong here:
`ichrisbirch/api/client/` covers those. So does OIDC discovery in
`api/oidc_auth.py`, which talks to the identity provider with its own user agent
and its own caller-supplied timeout.
"""

import httpx

from ichrisbirch.config import Settings

# Long, because the callers are fetching arbitrary pages a person asked to save
# and a slow site is a normal outcome rather than a fault. httpx's default of
# five seconds is tuned for an API you control.
DEFAULT_TIMEOUT = 30.0


def get_page(url: str, settings: Settings, timeout: float = DEFAULT_TIMEOUT) -> httpx.Response:
    """Fetch a third-party page as a browser would, following redirects.

    The response is returned unraised: a caller that wants a non-2xx to be an
    error calls `.raise_for_status()` on it, and a caller that wants to inspect
    the status itself still can.
    """
    return httpx.get(
        url,
        follow_redirects=True,
        headers=settings.mac_safari_request_headers,
        timeout=timeout,
    )
