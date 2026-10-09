"""The Authelia header strategy, through the real app and the real dependency chain.

The edge sends any bearer request to ichrisbirch.com past ForwardAuth, so `Remote-User` and
`Remote-Email` beside an `Authorization` header came from the client.
"""

import jwt
import pytest
from fastapi import status

from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from tests.factories import UserFactory
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
    ids=['junk-token', 'unknown-api-key', 'foreign-jwt'],
)
def test_a_rejected_bearer_never_falls_through_to_the_headers(txn_api, authorization):
    client, _ = txn_api
    response = client.get('/users/me/', headers=FORGED_HEADERS | {'Authorization': authorization})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)


def test_a_valid_bearer_beside_forged_headers_runs_as_the_bearer(txn_api):
    """The header strategy outranks a local JWT, so reading the headers here would run as the admin."""
    client, session = txn_api
    user = UserFactory(name='Bearer Holder', email='bearer-holder@test.com', password='bearer-holder-password')
    token = JWTTokenHandler(settings=test_settings, session=session).create_access_token(user.get_id())
    response = client.get('/users/me/', headers=FORGED_HEADERS | {'Authorization': f'Bearer {token}'})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json()['email'] == user.email
