"""Tests for the Authelia access-token verification the `icb` CLI authenticates with.

Every case runs against a real RSA key and a real JWKS served over HTTP, so the signature check,
the discovery lookup and PyJWKClient's key selection are all exercised rather than mocked out.
"""

import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from jwt.algorithms import RSAAlgorithm

from ichrisbirch.api import oidc_auth
from ichrisbirch.api.oidc_auth import OIDCTokenVerifier
from ichrisbirch.api.oidc_auth import OIDCVerificationError
from ichrisbirch.api.oidc_auth import bearer_token
from ichrisbirch.api.oidc_auth import build_verifier
from ichrisbirch.api.oidc_auth import discover_jwks_uri
from ichrisbirch.api.oidc_auth import get_oidc_identity
from ichrisbirch.api.oidc_auth import is_access_token

KEY_ID = 'main'
CLI_CLIENT_ID_PREFIX = 'icb-cli-'
CLI_CLIENT_ID = 'icb-cli-macmini'


class IdentityProviderStub:
    """A minimal Authelia stand-in serving a discovery document and a JWKS for one RSA key."""

    def __init__(self, key: rsa.RSAPrivateKey) -> None:
        self.key = key
        idp = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802  (BaseHTTPRequestHandler's required spelling)
                if self.path == '/.well-known/openid-configuration':
                    body = {'issuer': idp.url, 'jwks_uri': idp.url + '/jwks.json'}
                elif self.path == '/jwks.json':
                    body = idp.jwks()
                else:
                    self.send_error(404)
                    return
                payload = json.dumps(body).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                """Silence the default stderr access log."""

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def jwks(self) -> dict:
        public_jwk = RSAAlgorithm.to_jwk(self.key.public_key(), as_dict=True)
        return {'keys': [{**public_jwk, 'kid': KEY_ID, 'alg': 'RS256', 'use': 'sig'}]}

    def valid_claims(self) -> dict:
        now = int(time.time())
        return {
            'iss': self.url,
            'sub': 'authelia-user-uuid',
            'client_id': CLI_CLIENT_ID,
            'iat': now - 60,
            'exp': now + 3600,
        }

    def sign(self, claims: dict, token_type: str = 'at+jwt', key: rsa.RSAPrivateKey | None = None) -> str:
        return jwt.encode(claims, key or self.key, algorithm='RS256', headers={'typ': token_type, 'kid': KEY_ID})

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture(scope='module')
def signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope='module')
def foreign_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope='module')
def idp(signing_key) -> Iterator[IdentityProviderStub]:
    server = IdentityProviderStub(signing_key)
    yield server
    server.shutdown()


@pytest.fixture(autouse=True)
def clear_verifier_cache():
    """The process-wide verifier cache would otherwise carry one test's issuer into the next."""
    build_verifier.cache_clear()
    yield
    build_verifier.cache_clear()


@pytest.fixture
def verifier(idp) -> OIDCTokenVerifier:
    """Build the verifier through discovery, so the discovery lookup is under test too."""
    return OIDCTokenVerifier.from_discovery(idp.url, CLI_CLIENT_ID_PREFIX)


def make_request(authorization: str | None = None) -> Request:
    headers = [(b'authorization', authorization.encode())] if authorization else []
    scope = {
        'type': 'http',
        'method': 'GET',
        'scheme': 'http',
        'server': ('testserver', 80),
        'root_path': '',
        'path': '/tasks/',
        'query_string': b'',
        'headers': headers,
    }
    return Request(scope)


def oidc_settings(idp: IdentityProviderStub) -> SimpleNamespace:
    return SimpleNamespace(oidc=SimpleNamespace(issuer=idp.url, cli_client_id_prefix=CLI_CLIENT_ID_PREFIX))


class TestVerifyAccessToken:
    def test_accepts_a_valid_access_token(self, idp, verifier):
        identity = verifier.verify(idp.sign(idp.valid_claims()))
        assert identity.subject == 'authelia-user-uuid'
        assert identity.client_id == CLI_CLIENT_ID

    def test_rejects_an_id_token(self, idp, verifier):
        """An id_token is signed by the same key and carries the same issuer.

        Unlike the access token it is handed to the client, so only the header type separates them.
        """
        claims = idp.valid_claims() | {'aud': [CLI_CLIENT_ID]}
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims, token_type='JWT'))

    def test_rejects_a_foreign_signing_key(self, idp, verifier, foreign_key):
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(idp.valid_claims(), key=foreign_key))

    def test_rejects_an_expired_token(self, idp, verifier):
        claims = idp.valid_claims() | {'exp': int(time.time()) - 60}
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_a_wrong_issuer(self, idp, verifier):
        claims = idp.valid_claims() | {'iss': 'https://evil.example.com'}
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_another_products_client(self, idp, verifier):
        """Authelia leaves `aud` empty in the device grant, so isolation rests on this check."""
        claims = idp.valid_claims() | {'client_id': 'meso-cli-macmini'}
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_a_missing_subject(self, idp, verifier):
        claims = idp.valid_claims()
        del claims['sub']
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_an_empty_subject(self, idp, verifier):
        """PyJWT's `require` only checks presence, so an empty subject needs its own check."""
        claims = idp.valid_claims() | {'sub': ''}
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_a_missing_expiry(self, idp, verifier):
        claims = idp.valid_claims()
        del claims['exp']
        with pytest.raises(OIDCVerificationError):
            verifier.verify(idp.sign(claims))

    def test_rejects_a_token_signed_with_none(self, idp, verifier):
        claims = idp.valid_claims()
        unsigned = jwt.encode(claims, key='', algorithm='none', headers={'typ': 'at+jwt', 'kid': KEY_ID})
        with pytest.raises(OIDCVerificationError):
            verifier.verify(unsigned)


class TestDiscovery:
    def test_refuses_an_issuer_that_advertises_a_different_issuer(self, idp):
        with pytest.raises(ValueError, match='advertises itself as'):
            OIDCTokenVerifier.from_discovery(idp.url + '/', CLI_CLIENT_ID_PREFIX)


class TestBearerToken:
    @pytest.mark.parametrize(
        ('header', 'expected'),
        [
            ('Bearer abc.def.ghi', 'abc.def.ghi'),
            ('bearer abc.def.ghi', 'abc.def.ghi'),
            ('Basic dXNlcjpwdw==', ''),
            ('', ''),
            ('Bearer', ''),
            ('Bearer ', ''),
        ],
    )
    def test_extracts_only_a_bearer_credential(self, header, expected):
        assert bearer_token(header) == expected


class TestIsAccessToken:
    def test_recognises_an_access_token(self, idp):
        assert is_access_token(idp.sign(idp.valid_claims()))

    def test_rejects_an_id_token_and_anything_unparseable(self, idp):
        assert not is_access_token(idp.sign(idp.valid_claims(), token_type='JWT'))
        assert not is_access_token('icb_a_personal_api_key')
        assert not is_access_token('')


class TestGetOIDCIdentity:
    def test_returns_the_identity_for_a_valid_token(self, idp):
        request = make_request(f'Bearer {idp.sign(idp.valid_claims())}')
        identity = get_oidc_identity(request, oidc_settings(idp))
        assert identity is not None
        assert identity.client_id == CLI_CLIENT_ID

    @pytest.mark.parametrize(
        'authorization',
        [None, '', 'Basic dXNlcjpwdw==', 'Bearer icb_a_personal_api_key', 'Bearer not-a-jwt'],
    )
    def test_passes_other_credentials_through_untouched(self, idp, authorization):
        """A credential belonging to another strategy is not this one's to reject."""
        assert get_oidc_identity(make_request(authorization), oidc_settings(idp)) is None

    def test_a_locally_signed_jwt_is_left_to_the_legacy_strategy(self, idp):
        local = jwt.encode({'sub': '123'}, 'a-local-hs256-secret-of-at-least-32-bytes', algorithm='HS256')
        assert get_oidc_identity(make_request(f'Bearer {local}'), oidc_settings(idp)) is None

    @pytest.mark.parametrize(
        'claims_override',
        [
            {'client_id': 'meso-cli-macmini'},
            {'iss': 'https://evil.example.com'},
            {'exp': int(time.time()) - 60},
            {'sub': ''},
        ],
    )
    def test_rejects_a_failed_access_token_rather_than_falling_through(self, idp, claims_override):
        """A presented access token that fails verification must 401, never return None.

        Returning None would let a caller pair a junk token with a weaker credential and have the
        token quietly ignored.
        """
        token = idp.sign(idp.valid_claims() | claims_override)
        with pytest.raises(HTTPException) as exc_info:
            get_oidc_identity(make_request(f'Bearer {token}'), oidc_settings(idp))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_every_rejection_returns_the_same_opaque_detail(self, idp, foreign_key):
        claims_without_subject = idp.valid_claims()
        del claims_without_subject['sub']
        rejected = [
            idp.sign(idp.valid_claims(), key=foreign_key),
            idp.sign(idp.valid_claims() | {'client_id': 'meso-cli-macmini'}),
            idp.sign(claims_without_subject),
        ]
        details = set()
        for token in rejected:
            with pytest.raises(HTTPException) as exc_info:
                get_oidc_identity(make_request(f'Bearer {token}'), oidc_settings(idp))
            details.add(exc_info.value.detail)
        assert len(details) == 1


class TestUserAgent:
    """Cloudflare fronts the issuer and refuses an unidentified client."""

    def test_discovery_and_jwks_identify_themselves(self):
        """Measured 2026-08-14: the public hostname answers 403 to `Python-urllib/3.12`, which is
        what urllib and therefore PyJWKClient send by default, and 200 to a named agent. Reaching
        the provider by an internal address instead would tie verification to one network layout.
        """
        seen: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                seen.append(self.headers.get('User-Agent', ''))
                body = json.dumps({'issuer': self.server.issuer, 'jwks_uri': f'{self.server.issuer}/jwks.json'}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):  # noqa: ANN002
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.issuer = f'http://127.0.0.1:{server.server_port}'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            discover_jwks_uri(server.issuer)
        finally:
            server.shutdown()
            server.server_close()

        assert seen, 'discovery was never fetched'
        assert seen[0] == oidc_auth.USER_AGENT
        assert 'urllib' not in seen[0].lower()
