from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from tests.util import show_status_and_response

ENDPOINT = '/admin/settings/'


def stored_is_signup_open(session) -> bool:
    return session.scalars(select(models.AdminSettings.is_signup_open)).one()


def test_an_admin_opens_signups(txn_api_logged_in_admin):
    client, session = txn_api_logged_in_admin
    response = client.patch(ENDPOINT, json={'is_signup_open': True})
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert response.json() == {'is_signup_open': True}
    assert client.get(ENDPOINT).json() == {'is_signup_open': True}
    assert stored_is_signup_open(session) is True


def test_a_non_admin_cannot_open_signups(txn_api_logged_in):
    client, session = txn_api_logged_in
    response = client.patch(ENDPOINT, json={'is_signup_open': True})
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
    assert stored_is_signup_open(session) is False


def test_an_anonymous_caller_cannot_open_signups(txn_api):
    client, session = txn_api
    response = client.patch(ENDPOINT, json={'is_signup_open': True})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, show_status_and_response(response)
    assert stored_is_signup_open(session) is False


def test_a_non_admin_cannot_read_the_settings(txn_api_logged_in):
    client, _ = txn_api_logged_in
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_403_FORBIDDEN, show_status_and_response(response)
