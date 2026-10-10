"""The Authelia header strategy, through the real app and the real dependency chain.

The edge sends any bearer request to ichrisbirch.com past ForwardAuth, so `Remote-User` and
`Remote-Email` beside an `Authorization` header came from the client.
"""

import jwt
import pytest
from fastapi import status

from ichrisbirch.api.oidc_auth import OIDCIdentity
from ichrisbirch.api.oidc_auth import get_oidc_identity
from tests.util import show_status_and_response
from tests.utils.database import test_settings

ADMIN_EMAIL = 'testloginadmin@testadmin.com'
FORGED_HEADERS = {'Remote-User': 'testloginadmin', 'Remote-Email': ADMIN_EMAIL}


def test_the_headers_forwardauth_sets_resolve_the_account(txn_api):
    client, _ = txn_api
    response = client.get('/users/me/', headers=FORGED_HEADERS)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['email'] == ADMIN_EMAIL


@pytest.mark.parametrize(
    'authorization',
    [
        'Bearer forged.jwt.value',
        'Bearer icb_not_a_real_key',
        'Bearer ' + jwt.encode({'sub': '1'}, 'a-secret-this-api-never-signed-with', algorithm='HS256'),
    ],
    ids=['junk-token', 'personal-api-key', 'locally-signed-jwt'],
)
def test_a_rejected_bearer_never_falls_through_to_the_headers(txn_api, authorization):
    client, _ = txn_api
    response = client.get('/users/me/', headers=FORGED_HEADERS | {'Authorization': authorization})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


def test_a_valid_bearer_beside_forged_headers_runs_as_the_bearer(txn_api):
    """The headers name an admin who is not the CLI user, so reading them here would run as that admin."""
    client, _ = txn_api
    client.app.dependency_overrides[get_oidc_identity] = lambda: OIDCIdentity(subject='authelia-user-uuid', client_id='icb-cli-macmini')
    response = client.get('/users/me/', headers=FORGED_HEADERS | {'Authorization': 'Bearer a-verified-access-token'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['email'] == test_settings.oidc.cli_user_email
