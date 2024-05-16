import pytest
from fastapi import status

import tests.util
from tests import test_data
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')


@pytest.fixture
def test_app_logout_after(test_app):
    yield test_app
    test_app.get('/logout/', follow_redirects=True)


TEST_USER = test_data.users.BASE_DATA[0]
SIGNUP_USER = dict(name='Signup User', email='signup.user@aol.com', password='easypassword')


def test_login_page(test_app):
    response = test_app.get('/login/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Login for iChrisBirch</title>' in response.data


def test_signup_page(test_app):
    response = test_app.get('/signup/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Signup for iChrisBirch</title>' in response.data


def test_do_signup(test_app_logout_after):
    response = test_app_logout_after.post(
        '/signup/', follow_redirects=True, data=SIGNUP_USER | {'confirm_password': SIGNUP_USER['password']}
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert f'<title>Welcome, {SIGNUP_USER['name']}</title>' in response.text


def test_do_login(test_app_logout_after):
    response = test_app_logout_after.post(
        '/login/', follow_redirects=True, data={'email': TEST_USER.email, 'password': TEST_USER.password}
    )
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert f'<title>Welcome, {TEST_USER.name}</title>' in response.text


def test_login_wrong_password(test_app, caplog):
    test_app.post('/login/', follow_redirects=True, data={'email': TEST_USER.email, 'password': 'wrong_password'})
    assert f'invalid login attempt for: {TEST_USER.email}' in caplog.text


def test_duplicate_signup_error(test_app, caplog):
    test_app.post(
        '/signup/',
        follow_redirects=True,
        data={
            'name': TEST_USER.name,
            'email': TEST_USER.email,
            'password': TEST_USER.password,
            'confirm_password': TEST_USER.password,
        },
    )
    assert 'duplicate email registration attempt' in caplog.text
