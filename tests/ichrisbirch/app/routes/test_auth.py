import pytest
from fastapi import status

import tests.util
from tests import test_data
from tests.util import show_status_and_response


@pytest.fixture(autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')


TEST_USER = test_data.users.BASE_DATA[0]
SIGNUP_USER = {
    'name': 'Signup User',
    'email': 'signup.user@gmail.com',
    'password': 'easypa_$ssword',
    'confirm_password': 'easypa_$ssword',
}


def test_login_page(test_app):
    response = test_app.get('/login/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Login for iChrisBirch</title>' in response.data


def test_signup_page(test_app):
    response = test_app.get('/signup/')
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert b'<title>Signup for iChrisBirch</title>' in response.data


@pytest.mark.skip('db error')
def test_do_login(test_app):
    login_data = {'email': TEST_USER.email, 'password': TEST_USER.password}
    response = test_app.post('/login/', follow_redirects=True, data=login_data)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert f'<title>Welcome, {TEST_USER.name}</title>' in response.text
    test_app.get('/logout/', follow_redirects=True)


@pytest.mark.skip('db error')
def test_do_signup(test_app):
    response = test_app.post('/signup/', follow_redirects=True, data=SIGNUP_USER)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    assert f'<title>Welcome, {SIGNUP_USER['name']}</title>' in response.text


@pytest.mark.skip('db error')
def test_login_wrong_password(test_app, caplog):
    test_app.post('/login/', follow_redirects=True, data={'email': TEST_USER.email, 'password': 'wrong_password'})
    assert f'invalid login attempt for: {TEST_USER.email}' in caplog.text, 'No error log produced'


@pytest.mark.skip('db error')
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
