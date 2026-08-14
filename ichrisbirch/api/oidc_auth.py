"""Verification of the RFC 9068 JWT access tokens Authelia issues to the `icb` CLI.

The CLI logs in with the OAuth 2.0 device authorization grant, which rules out Authelia's
`authelia.bearer.authz` scope, so the token is no longer authorized at the Traefik ForwardAuth edge.
It is a signed JWT and the API verifies it in-process against Authelia's JWKS.

Key retrieval, caching and rotation are PyJWT's `PyJWKClient`. Nothing here parses a JWT by hand.
"""

import functools
from urllib.parse import urlparse

import httpx
import jwt
import structlog
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from pydantic import BaseModel

from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings

logger = structlog.get_logger()

ACCESS_TOKEN_TYPE = 'at+jwt'
SIGNING_ALGORITHM = 'RS256'
DISCOVERY_PATH = '/.well-known/openid-configuration'
DISCOVERY_TIMEOUT_SECONDS = 10.0

# Every rejection returns this, so a probe cannot use the response to learn which check it failed.
# The reason is logged instead.
UNAUTHORIZED_DETAIL = 'Invalid credentials'
PROVIDER_UNAVAILABLE_DETAIL = 'Identity provider unavailable'


class OIDCVerificationError(Exception):
    """A token failed one of the checks. The message is for the log, never for the caller."""


class OIDCProviderUnavailable(Exception):
    """Authelia could not be reached, so the token was never judged.

    Distinct from a rejection: answering 401 here tells a caller holding a good token to log in
    again, and a re-login cannot fix a network failure.
    """


class OIDCIdentity(BaseModel):
    """What a verified access token establishes about the caller."""

    subject: str
    client_id: str


def bearer_token(authorization_header: str) -> str:
    """Return the credential from an Authorization header, or '' for an absent or non-Bearer one."""
    scheme, _, credential = authorization_header.partition(' ')
    if scheme.lower() != 'bearer':
        return ''
    return credential.strip()


def is_access_token(token: str) -> bool:
    """Report whether the token declares itself an RFC 9068 access token.

    This routes rather than authorizes — it decides whether a bearer credential belongs to this
    strategy at all, so a Personal API Key or a locally-signed HS256 JWT is left to the strategy
    that owns it. The same check runs again inside `OIDCTokenVerifier.verify`, where it is
    load-bearing.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        return False
    return str(header.get('typ', '')).lower() == ACCESS_TOKEN_TYPE


def discover_jwks_uri(issuer: str, internal_url: str = '', timeout: float = DISCOVERY_TIMEOUT_SECONDS) -> str:
    """Resolve the issuer's JWKS endpoint from its OIDC discovery document.

    `internal_url` reaches the provider without leaving the network. The public hostname resolves
    to Cloudflare, which answers 403 to `Python-urllib` — the user agent PyJWKClient fetches with —
    while allowing Go's and curl's. Measured 2026-08-14. Routing a service-to-service call out to
    the internet and back also makes token verification depend on a bot rule nobody here controls.

    The issuer string is unchanged either way: it identifies the provider and must keep matching
    the `iss` claim, so only the transport moves.
    """
    base = (internal_url or issuer).rstrip('/')
    response = httpx.get(base + DISCOVERY_PATH, timeout=timeout)
    response.raise_for_status()
    document = response.json()

    if document.get('issuer') != issuer:
        raise ValueError(f'issuer {issuer!r} advertises itself as {document.get("issuer")!r}')
    if not (jwks_uri := document.get('jwks_uri')):
        raise ValueError(f'issuer {issuer!r} advertises no jwks_uri')
    if internal_url:
        jwks_uri = base + urlparse(jwks_uri).path
    return jwks_uri


class OIDCTokenVerifier:
    """Checks a token's signature against the issuer's JWKS and its claims against this API."""

    def __init__(self, issuer: str, cli_client_id_prefix: str, jwk_client: jwt.PyJWKClient) -> None:
        self.issuer = issuer
        self.cli_client_id_prefix = cli_client_id_prefix
        self.jwk_client = jwk_client

    @classmethod
    def from_discovery(cls, issuer: str, cli_client_id_prefix: str, internal_url: str = '') -> 'OIDCTokenVerifier':
        jwks_uri = discover_jwks_uri(issuer, internal_url)
        return cls(issuer, cli_client_id_prefix, jwt.PyJWKClient(jwks_uri, cache_keys=True))

    def verify(self, token: str) -> OIDCIdentity:
        """Verify a token and return the identity it establishes, or raise OIDCVerificationError."""
        self._require_access_token_type(token)

        try:
            signing_key = self.jwk_client.get_signing_key_from_jwt(token)
        except jwt.exceptions.PyJWKClientConnectionError as exc:
            raise OIDCProviderUnavailable(f'JWKS fetch failed: {exc}') from exc
        except jwt.PyJWTError as exc:
            raise OIDCVerificationError(f'no signing key for this token: {exc}') from exc

        try:
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=[SIGNING_ALGORITHM],
                issuer=self.issuer,
                # `aud` is empty on every token the device grant produces, so there is nothing to
                # match and PyJWT would reject a token whose aud it cannot be told to expect.
                options={'verify_aud': False, 'require': ['exp', 'iss', 'sub']},
            )
        except jwt.PyJWTError as exc:
            raise OIDCVerificationError(f'{type(exc).__name__}: {exc}') from exc

        subject = claims.get('sub') or ''
        if not subject:
            raise OIDCVerificationError('token carries no subject')

        client_id = claims.get('client_id')
        # A non-string claim would raise AttributeError out of startswith, which is not a rejection
        # and would surface as a 500 rather than the opaque 401 every other failure returns.
        if not isinstance(client_id, str) or not client_id.startswith(self.cli_client_id_prefix):
            raise OIDCVerificationError(f'client {client_id!r} is not a {self.cli_client_id_prefix}* client')

        return OIDCIdentity(subject=subject, client_id=client_id)

    def _require_access_token_type(self, token: str) -> None:
        """Reject anything not typed as an RFC 9068 access token.

        An id_token from the same issuer carries a valid signature and the same issuer, so without
        this check it would authenticate — and unlike the access token it is handed to the client
        rather than kept from it.
        """
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise OIDCVerificationError(f'token header is unreadable: {exc}') from exc

        token_type = str(header.get('typ', ''))
        if token_type.lower() != ACCESS_TOKEN_TYPE:
            raise OIDCVerificationError(f'token type {token_type!r} is not {ACCESS_TOKEN_TYPE}')


@functools.cache
def build_verifier(issuer: str, cli_client_id_prefix: str, internal_url: str = '') -> OIDCTokenVerifier:
    """Return the process-wide verifier for an issuer, resolving discovery on first use.

    Cached on the two strings rather than on Settings so a failed discovery is not memoised —
    `functools.cache` stores results, not exceptions, so Authelia being down at the first request
    does not poison every later one.
    """
    return OIDCTokenVerifier.from_discovery(issuer, cli_client_id_prefix, internal_url)


def get_oidc_identity(request: Request, settings: Settings = Depends(get_settings)) -> OIDCIdentity | None:
    """FastAPI dependency resolving a verified `icb` CLI access token to its identity.

    Returns None when the request carries no access token, which is how every other caller — the
    browser SPA, an internal service, a Personal API Key client — passes through untouched. A
    request that does present an access token and fails verification raises 401 here rather than
    returning None, so it can never fall through to a strategy that would accept it.
    """
    token = bearer_token(request.headers.get('Authorization', ''))
    if not token or not is_access_token(token):
        return None

    try:
        verifier = build_verifier(settings.oidc.issuer, settings.oidc.cli_client_id_prefix, settings.oidc.internal_url)
        identity = verifier.verify(token)
    except (OIDCProviderUnavailable, httpx.HTTPError) as exc:
        logger.error('oidc_provider_unreachable', error=str(exc), path=request.url.path)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=PROVIDER_UNAVAILABLE_DETAIL) from None
    except (OIDCVerificationError, ValueError) as exc:
        logger.warning('oidc_bearer_rejected', error=str(exc), path=request.url.path)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=UNAUTHORIZED_DETAIL) from None

    logger.debug('oidc_bearer_verified', subject=identity.subject, client_id=identity.client_id)
    return identity
