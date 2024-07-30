import pytest
from fastapi import status

import tests.util
from tests import test_data
from tests.util import show_status_and_response


@pytest.fixture(scope='function', autouse=True)
def insert_testing_data():
    tests.util.insert_test_data('users')
    yield
    tests.util.delete_test_data('users')


@pytest.fixture()
def test_app_with_logout_function(test_app_function):
    yield test_app_function
    test_app_function.get('/logout/')


TEST_USER = test_data.users.BASE_DATA[0]
SIGNUP_USER = {
    'name': 'Signup User',
    'email': 'signup.user@gmail.com',
    'password': 'easypa_$ssword',
    'confirm_password': 'easypa_$ssword',
}


class TestLogin:
    def test_login_page(self, test_app_function):
        response = test_app_function.get('/login/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'<title>Login for iChrisBirch</title>' in response.data

    def test_login_page_redirects_for_logged_in_user(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get('/login/')
        assert response.status_code == status.HTTP_302_FOUND, show_status_and_response(response)
        assert '/users/profile/' in response.headers['Location']

    def test_do_login(self, test_app_function):
        login_data = {'email': TEST_USER.email, 'password': TEST_USER.password}
        response = test_app_function.post('/login/', follow_redirects=True, data=login_data)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert f'<title>Welcome, {TEST_USER.name}</title>' in response.text

    def test_login_wrong_password(self, test_app_function, caplog):
        test_app_function.post(
            '/login/', follow_redirects=True, data={'email': TEST_USER.email, 'password': 'wrong_password'}
        )
        assert f'invalid login attempt for: {TEST_USER.email}' in caplog.text, 'No error log produced'


class TestSignup:
    def test_signup_page(self, test_app_logged_in_function):
        response = test_app_logged_in_function.get('/signup/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert b'<title>Signup for iChrisBirch</title>' in response.data

    def test_do_signup(self, test_app_function):
        response = test_app_function.post('/signup/', follow_redirects=True, data=SIGNUP_USER)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert f'<title>Welcome, {SIGNUP_USER['name']}</title>' in response.text

    def test_duplicate_signup_error(self, test_app_function, caplog):
        test_app_function.post(
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
